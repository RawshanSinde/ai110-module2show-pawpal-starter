import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler, DailyPlan

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

# --- Session state initialization ---
if "owner" not in st.session_state:
    st.session_state.owner = None

if "pet" not in st.session_state:
    st.session_state.pet = None

# --- Owner & Pet Setup ---
st.subheader("Owner & Pet")

col1, col2 = st.columns(2)
with col1:
    owner_name = st.text_input("Owner name", value="Jordan")
    available_minutes = st.number_input("Daily time budget (min)", min_value=10, max_value=480, value=90)
with col2:
    pet_name = st.text_input("Pet name", value="Mochi")
    species = st.selectbox("Species", ["dog", "cat", "other"])
    age = st.number_input("Pet age", min_value=0, max_value=30, value=2)
    special_needs = st.text_input("Special needs (comma-separated, or leave blank)")

if st.button("Save Owner & Pet"):
    owner = Owner(name=owner_name, available_minutes=int(available_minutes), preferences={})
    needs_list = [s.strip() for s in special_needs.split(",") if s.strip()]
    pet = Pet(name=pet_name, species=species, age=int(age), special_needs=needs_list)
    owner.add_pet(pet)
    st.session_state.owner = owner
    st.session_state.pet = pet
    st.success(f"Saved {owner_name} and {pet_name}!")

if st.session_state.owner:
    owner = st.session_state.owner
    pet = st.session_state.pet
    st.caption(f"Current: {owner.name} | {pet.name} ({pet.species}, age {pet.age}) | Budget: {owner.available_minutes} min")

st.divider()

# --- Add Tasks ---
st.subheader("Add a Task")

if st.session_state.pet is None:
    st.info("Save an owner and pet above before adding tasks.")
else:
    col1, col2, col3 = st.columns(3)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
        category = st.text_input("Category", value="exercise")
    with col2:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
        is_required = st.checkbox("Required today?", value=True)
    with col3:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
        notes = st.text_input("Notes (optional)", value="")

    if st.button("Add Task"):
        task = Task(
            title=task_title,
            duration_minutes=int(duration),
            priority=priority,
            category=category,
            is_required=is_required,
            notes=notes
        )
        st.session_state.pet.add_task(task)
        st.success(f"Added: {task_title}")

    current_tasks = st.session_state.pet.get_task_list()
    if current_tasks:
        st.markdown(f"**{st.session_state.pet.name}'s tasks ({len(current_tasks)})**")
        st.table([{
            "Title": t.title,
            "Duration": f"{t.duration_minutes} min",
            "Priority": t.priority,
            "Category": t.category,
            "Required": t.is_required
        } for t in current_tasks])
    else:
        st.info("No tasks yet. Add one above.")

st.divider()

# --- Generate Schedule ---
st.subheader("Build Schedule")

if st.session_state.owner is None:
    st.info("Save an owner and pet above before generating a schedule.")
elif not st.session_state.pet.get_task_list():
    st.info("Add at least one task before generating a schedule.")
else:
    if st.button("Generate Schedule"):
        owner = st.session_state.owner
        pet = st.session_state.pet
        all_tasks = owner.get_all_tasks()
        scheduler = Scheduler(owner=owner, tasks=all_tasks)
        plan = scheduler.generate_plan()

        free = owner.available_minutes - plan.total_duration
        st.markdown(f"**Budget:** {owner.available_minutes} min | **Used:** {plan.total_duration} min | **Free:** {free} min")

        st.markdown("#### Scheduled")
        for task in plan.scheduled_tasks:
            label = "🔴 required" if task.is_required else "🔵 optional"
            st.markdown(f"- **{task.title}** — {task.duration_minutes} min | {task.category} | {label}")

        if plan.skipped_tasks:
            st.markdown("#### Skipped (not enough time)")
            for task in plan.skipped_tasks:
                st.markdown(f"- {task.title} — {task.duration_minutes} min")

        st.info(plan.explanation)
