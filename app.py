import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler, DailyPlan

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

# --- Session state initialization ---
if "owner" not in st.session_state:
    st.session_state.owner = None

if "pet" not in st.session_state:
    st.session_state.pet = None

if "editing_task" not in st.session_state:
    st.session_state.editing_task = None

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
        time_of_day = st.selectbox("Time of day", ["(none)", "morning", "afternoon", "evening"])
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
            notes=notes,
            time_of_day=None if time_of_day == "(none)" else time_of_day,
        )
        st.session_state.pet.add_task(task)
        st.success(f"Added: {task_title}")

    current_tasks = st.session_state.pet.get_task_list()
    if current_tasks:
        owner = st.session_state.owner
        scheduler = Scheduler(owner=owner, tasks=current_tasks)
        sorted_tasks = scheduler.sort_by_time(scheduler.filter_by_status(current_tasks))

        st.markdown(f"**{st.session_state.pet.name}'s tasks — sorted by time slot ({len(sorted_tasks)} active)**")

        for i, t in enumerate(sorted_tasks):
            col_info, col_edit, col_del = st.columns([5, 1, 1])
            with col_info:
                slot = t.time_of_day or "—"
                req = "required" if t.is_required else "optional"
                st.markdown(f"**{t.title}** &nbsp; `{t.priority.upper()}` &nbsp; {t.duration_minutes} min &nbsp; {slot} &nbsp; {t.category} &nbsp; *{req}*")
            with col_edit:
                if st.button("Edit", key=f"edit_{i}"):
                    st.session_state.editing_task = t
                    st.rerun()
            with col_del:
                if st.button("Del", key=f"del_{i}"):
                    if st.session_state.editing_task is t:
                        st.session_state.editing_task = None
                    st.session_state.pet.tasks.remove(t)
                    st.rerun()

        # Inline edit form
        if st.session_state.editing_task is not None:
            task = st.session_state.editing_task
            st.markdown("---")
            st.markdown(f"#### Editing: *{task.title}*")
            with st.form("edit_task_form"):
                ec1, ec2, ec3 = st.columns(3)
                with ec1:
                    new_title = st.text_input("Task title", value=task.title)
                    new_category = st.text_input("Category", value=task.category)
                    slot_options = ["(none)", "morning", "afternoon", "evening"]
                    slot_index = slot_options.index(task.time_of_day) if task.time_of_day in slot_options else 0
                    new_slot = st.selectbox("Time of day", slot_options, index=slot_index)
                with ec2:
                    new_duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=task.duration_minutes)
                    new_required = st.checkbox("Required today?", value=task.is_required)
                with ec3:
                    pri_options = ["low", "medium", "high"]
                    new_priority = st.selectbox("Priority", pri_options, index=pri_options.index(task.priority))
                    new_notes = st.text_input("Notes (optional)", value=task.notes)

                save_col, cancel_col = st.columns(2)
                with save_col:
                    submitted = st.form_submit_button("Save changes")
                with cancel_col:
                    cancelled = st.form_submit_button("Cancel")

            if submitted:
                task.title = new_title
                task.duration_minutes = int(new_duration)
                task.priority = new_priority
                task.category = new_category
                task.is_required = new_required
                task.notes = new_notes
                task.time_of_day = None if new_slot == "(none)" else new_slot
                st.session_state.editing_task = None
                st.rerun()

            if cancelled:
                st.session_state.editing_task = None
                st.rerun()
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
        all_tasks = owner.get_all_tasks()
        scheduler = Scheduler(owner=owner, tasks=all_tasks)
        plan = scheduler.generate_plan()

        # Budget metrics
        free = owner.available_minutes - plan.total_duration
        m1, m2, m3 = st.columns(3)
        m1.metric("Budget", f"{owner.available_minutes} min")
        m2.metric("Used", f"{plan.total_duration} min")
        m3.metric("Free", f"{free} min")

        st.divider()

        # Conflicts
        if plan.conflicts:
            st.markdown("#### Conflicts")
            for conflict in plan.conflicts:
                st.warning(conflict)

        # Scheduled tasks
        if plan.scheduled_tasks:
            st.markdown("#### Scheduled tasks")
            st.table([{
                "Title": t.title,
                "Slot": t.time_of_day or "—",
                "Duration": f"{t.duration_minutes} min",
                "Priority": t.priority.upper(),
                "Category": t.category,
                "Required": "yes" if t.is_required else "no",
            } for t in plan.scheduled_tasks])

        # Skipped tasks
        if plan.skipped_tasks:
            st.markdown("#### Skipped (not enough time)")
            for task in plan.skipped_tasks:
                st.warning(f"{task.title} — {task.duration_minutes} min | {task.priority} priority")

        # Explanation
        if not plan.skipped_tasks and not plan.conflicts:
            st.success(plan.explanation)
        else:
            st.info(plan.explanation)
