from aiogram.fsm.state import State, StatesGroup


class RegistrationStates(StatesGroup):
    waiting_for_full_name = State()
    waiting_for_school = State()


class SearchStates(StatesGroup):
    waiting_for_query = State()
    waiting_for_custom_question = State()


class SuggestionStates(StatesGroup):
    waiting_for_event_format = State()
    waiting_for_event_text = State()
    waiting_for_method_problem = State()
    waiting_for_method_solution = State()
    waiting_for_method_result = State()
