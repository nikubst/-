from aiogram.fsm.state import State, StatesGroup

class JobApplicationStates(StatesGroup):
    agree_rules = State()
    full_name = State()
    phone = State()
    national_id = State()
    city = State()
    age = State()
    job_position = State()
    experience = State()
    skills = State()
    documents = State()
    confirm = State()

class TrackApplicationStates(StatesGroup):
    enter_code = State()

class SupplementaryDocsStates(StatesGroup):
    app_id = State()
    documents = State()

class AddProductStates(StatesGroup):
    code = State()
    title = State()
    category = State()
    dimensions = State()
    raj_shomar = State()
    pattern_name = State()
    material = State()
    price = State()
    marketing_pitch = State()
    photos = State()
    confirm = State()

class AdminReviewStates(StatesGroup):
    app_id = State()
    need_info_reason = State()
    reject_reason = State()

class BroadcastStates(StatesGroup):
    target = State()
    message = State()
