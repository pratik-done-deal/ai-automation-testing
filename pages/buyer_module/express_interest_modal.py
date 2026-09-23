import re

from playwright.sync_api import expect

from constants import Copy
from pages.shared.base_page import BasePage
from pages.buyer_module.interest_shared_modal import InterestSharedModal


class ExpressInterestModal(BasePage):
    """Step 1 of the buyer flow: SlotSchedulerModal (date -> time -> note -> Request Call)."""

    def wait_until_open(self):
        expect(self.page.get_by_text(re.compile(Copy.SLOT_LABEL, re.I))).to_be_visible(timeout=15_000)

    @property
    def slot_label(self):
        return self.page.get_by_text(re.compile(Copy.SLOT_LABEL, re.I)).first

    @property
    def request_call_button(self):
        return self.page.get_by_role("button", name=re.compile(rf"^({Copy.REQUEST_CALL}|Connect)$"))

    @property
    def cancel_button(self):
        return self.page.get_by_role("button", name=Copy.CANCEL, exact=True).first

    @property
    def note_label(self):
        return self.page.get_by_text(Copy.NOTE_LABEL)

    @property
    def note_input(self):
        return self.page.locator("textarea:not([aria-hidden='true'])").first

    # --- calendar (MUI StaticDatePicker with disablePast) ---

    def enabled_days(self):
        return self.page.locator("button.MuiPickersDay-root:not(.MuiPickersDay-hiddenDaySpacingFiller):not([disabled])")

    def past_days(self):
        return self.page.locator("button.MuiPickersDay-root[disabled]")

    SLOTS_API = re.compile(r"meeting/(suggested/)?slots/buyer")

    def pick_first_available_date(self, index=0):
        day = self.enabled_days().nth(index)
        expect(day).to_be_visible()
        # The time view (with "No slots available" from the previous state) renders before the
        # slots request returns, so wait for that response before reading the times.
        with self.page.expect_response(lambda r: self.SLOTS_API.search(r.url), timeout=30_000):
            day.click()
        expect(self.back_link).to_be_visible()
        self.page.wait_for_timeout(500)  # let React render the fetched slots

    @property
    def back_link(self):
        # Only the arrow icon before the "Back" label is clickable (TimeSlotsV2.js:22-26).
        return self.page.get_by_text("Back", exact=True).locator("xpath=preceding-sibling::div[1]")

    # --- time slots (TimeSlotsV2) ---

    def available_times(self):
        # Bookable slots carry `cursor-pointer`; booked ones `cursor-not-allowed`.
        return self.page.locator("div.grid div.cursor-pointer span")

    @property
    def no_slots_message(self):
        return self.page.get_by_text("No slots available for this date.")

    @property
    def confirm_selection_button(self):
        return self.page.get_by_role("button", name="Confirm selection")

    def pick_first_available_time(self, index=0) -> str:
        time_cell = self.available_times().nth(index)
        expect(time_cell).to_be_visible()
        label = time_cell.inner_text().strip()
        time_cell.click()
        self.confirm_selection_button.click()
        return label

    def pick_date_with_times(self, min_times=1, max_days=10):
        """Open the first date offering at least `min_times` free times; leaves the time view open."""
        for index in range(max_days):
            self.pick_first_available_date(index)
            expect(self.available_times().first.or_(self.no_slots_message)).to_be_visible(timeout=15_000)
            if self.available_times().count() >= min_times:
                return
            self.back_link.click()  # today is often fully booked late in the day
        raise AssertionError(f"No date with {min_times} free time(s) in the next {max_days} selectable days")

    def add_slot(self, time_index=0):
        """Choose the first date with free times, then its `time_index`-th time; returns the time label."""
        self.pick_date_with_times(min_times=time_index + 1)
        return self.pick_first_available_time(time_index)

    # --- goal of conversation (shown only for some buyer types) ---

    def select_goal_if_required(self, goal="Investment"):
        if self.page.get_by_text("Goal of conversation").count():
            self.page.get_by_text(goal, exact=True).first.click()

    def selected_slot_rows(self):
        return self.page.get_by_text(re.compile(r"^\d{2}/\d{2}/\d{4}$"))

    def add_second_slot(self, time_index=1):
        # A second slot with the same date and time is rejected as a duplicate, so pick another time.
        self.page.get_by_text(Copy.ADD_SECOND_SLOT).click()
        return self.add_slot(time_index)

    # --- "Your interest has not been sent..." confirmation (ModalWithTwoCTAs, cancelLabel="Back") ---

    @property
    def cancel_confirmation(self):
        return self.page.get_by_text("Your interest has not been sent to the company yet")

    @property
    def cancel_confirmation_back(self):
        return self.page.get_by_role("button", name="Back", exact=True)

    def fill_note(self, text):
        self.note_input.fill(text)

    def submit(self) -> InterestSharedModal:
        """Click Request Call; the returned success view carries `capture_request` / `capture_response`."""
        self.select_goal_if_required()
        is_capture = lambda r: r.url.rstrip("/").endswith("deal/capture/interest")  # noqa: E731
        with self.page.expect_response(is_capture, timeout=30_000) as res_info:
            self.request_call_button.click()
        success = InterestSharedModal(self.page)
        success.capture_request = res_info.value.request.post_data_json
        success.capture_response = res_info.value.json()
        success.wait_until_open()
        return success
