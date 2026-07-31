import os

# Work around a macOS OpenMP conflict between faiss and other native libs.
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

from dotenv import load_dotenv

load_dotenv()  # make GROQ_API_KEY available for the PawPal+ AI agent (ChatGroq)

import streamlit as st
from datetime import datetime, date, time as dtime

from pawpal_system import Owner, Pet, Task, Scheduler


@st.cache_resource(show_spinner="Loading PawPal+ AI agent (embeddings + FAISS)...")
def _get_pawpal_agent():
    """Build the RAG + LangGraph + Groq agent once and reuse across reruns."""
    from src.agent import PawPalAgent  # lazy import so the app starts fast

    return PawPalAgent()

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown("**A smart pet care planning assistant**")
st.caption("Organize your pets and schedule their care tasks efficiently.")

# --- Persist an Owner object in session_state so it survives reruns ---
if "owner" not in st.session_state:
    # Persist exactly one Owner object across reruns
    st.session_state.owner = Owner(name="Jordan")
else:
    # Owner is already initialized; will update name below
    pass

owner: Owner = st.session_state.owner

st.subheader("Owner Info")
owner_name = st.text_input("Owner name", value=owner.name, key="owner_name_input")
owner.name = owner_name

st.divider()

# --- Add Pet form (uses Owner.add_pet) ---
st.markdown("### Add Pet")
with st.form("add_pet_form", clear_on_submit=True):
    new_pet_name = st.text_input("Pet name", key="add_pet_name_input")
    new_species = st.selectbox("Species", ["dog", "cat", "other"], key="add_pet_species_input")
    new_age = st.number_input("Age (years)", min_value=0, max_value=50, value=1, key="add_pet_age_input")
    submitted = st.form_submit_button("Add pet")
    if submitted:
        if new_pet_name.strip():
            # Create a real Pet and add it to the single persisted Owner
            pet = Pet(name=new_pet_name, species=new_species, age=int(new_age))
            owner.add_pet(pet)
            st.success(f"Added pet: {pet.name} ({pet.species})")
        else:
            st.error("Pet name cannot be empty.")

# Show owner's pets
pets = owner.get_pets()
if pets:
    st.markdown("**Pets**")
    pet_cols = st.columns([2, 1.5, 1, 1.5])
    with pet_cols[0]:
        st.write("**Name**")
    with pet_cols[1]:
        st.write("**Species**")
    with pet_cols[2]:
        st.write("**Age**")
    with pet_cols[3]:
        st.write("**Tasks**")
    
    for p in pets:
        pet_cols = st.columns([2, 1.5, 1, 1.5])
        with pet_cols[0]:
            st.write(p.name)
        with pet_cols[1]:
            st.write(p.species.capitalize())
        with pet_cols[2]:
            st.write(str(p.age))
        with pet_cols[3]:
            st.write(str(len(p.get_tasks())))
else:
    st.info("No pets yet. Add a pet using the form above.")

st.divider()

# --- Pet Tasks Overview ---
st.subheader("Current Tasks by Pet")
pets = owner.get_pets()
if not pets:
    st.info("No pets yet. Add a pet to get started.")
else:
    for pet in pets:
        tasks = pet.get_tasks(include_completed=False)
        with st.expander(f"**{pet.name}** — {len(tasks)} task(s)", expanded=False):
            if tasks:
                for task in tasks:
                    priority_color = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(task.priority, "⚪")
                    due_text = task.due_date.strftime("%Y-%m-%d") if task.due_date else "No due date"
                    st.write(f"{priority_color} {task.description} — Due: {due_text}")
            else:
                st.caption("No pending tasks")

st.divider()

st.subheader("Add Task")
pets = owner.get_pets()
if not pets:
    st.info("No pets available — add a pet first.")
else:
    pet_names = [p.name for p in pets]
    with st.form("add_task_form", clear_on_submit=True):
        selected_pet_name = st.selectbox("For pet", pet_names, key="task_pet_select")
        task_desc = st.text_input("Task description", key="task_desc_input")
        task_date = st.date_input("Due date", value=date.today(), key="task_date_input")
        task_time = st.time_input("Time", value=dtime(hour=8, minute=0), key="task_time_input")
        task_duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=10, key="task_duration_input")
        task_priority = st.selectbox("Priority", ["low", "medium", "high"], index=1, key="task_priority_input")
        task_frequency = st.selectbox("Frequency", ["none", "daily", "weekly"], index=0, key="task_frequency_input")
        add_task = st.form_submit_button("Add task")
        if add_task:
            if task_desc.strip():
                pet_obj = next((p for p in pets if p.name == selected_pet_name), None)
                if pet_obj is None:
                    st.error("Selected pet not found.")
                else:
                    # Build a proper datetime for the task's due_date
                    due_dt = datetime.combine(task_date, task_time)
                    # Match the Task constructor fields in pawpal_system.py
                    task = Task(
                        description=task_desc,
                        time=task_time,
                        frequency=(None if task_frequency == "none" else task_frequency),
                        due_date=due_dt,
                        priority=task_priority,
                        duration_minutes=int(task_duration),
                    )
                    # Add the Task to the selected Pet
                    pet_obj.add_task(task)
                    st.success(f'Added task "{task_desc}" to {pet_obj.name}')
            else:
                st.error("Task description cannot be empty.")

st.divider()

# --- Build Schedule section (calls Scheduler.generate_plan) ---
st.subheader("Generate Schedule")
st.caption("Select a date and click to view the scheduled tasks for that day.")
schedule_date = st.date_input("Schedule date", value=date.today(), key="schedule_date_input")

if st.button("Generate schedule", key="generate_schedule_button"):
    if not owner.get_pets():
        st.warning("Add at least one pet and a task to generate a schedule.")
    else:
        sched = Scheduler(owner=owner, pets=owner.get_pets())
        plan = sched.generate_plan(datetime.combine(schedule_date, dtime.min))
        if plan:
            st.success("Schedule generated successfully!")
        # Show only tasks that are relevant for the selected schedule date.
        daily_plan = [
            item
            for item in plan
            if item.get("due_date") is not None and item["due_date"].date() == schedule_date
        ]

        if not daily_plan:
            st.info("No tasks scheduled for that date.")
        else:

            formatted_plan = []
            for item in daily_plan:
                time_text = item.get("time").strftime("%H:%M") if item.get("time") else "Anytime"
                due_text = item.get("due_date").strftime("%Y-%m-%d") if item.get("due_date") else "No due date"
                formatted_plan.append(
                    {
                        "Time": time_text,
                        "Pet": item.get("pet", "Unknown"),
                        "Task": item.get("description", ""),
                        "Priority": item.get("priority", "").capitalize(),
                        "Due": due_text,
                    }
                )

            st.markdown("### 📋 Schedule for " + schedule_date.strftime("%A, %B %d, %Y"))
            st.table(formatted_plan)

            conflicts = sched.detect_conflicts(daily_plan)
            if conflicts:
                for warning in conflicts:
                    st.warning(warning)

            with st.expander("📝 Scheduling Rationale"):
                st.text(sched.explain_plan(daily_plan))
        # End schedule generation

st.divider()

# --- AI Care Plan (PawPal+) ---------------------------------------------------
st.subheader("🧠 AI Care Plan (PawPal+)")
st.caption("Breed-aware daily care planning powered by RAG + LangGraph + Groq.")

ai_pets = owner.get_pets()
if not ai_pets:
    st.info("Add a pet above to generate an AI care plan.")
else:
    ai_pet_names = [p.name for p in ai_pets]
    selected_ai_pet_name = st.selectbox("Select a pet", ai_pet_names, key="ai_pet_select")
    selected_pet = next((p for p in ai_pets if p.name == selected_ai_pet_name), None)

    col_a, col_b = st.columns(2)
    with col_a:
        # Breed isn't tracked on Pet (only species) — let the user optionally
        # provide it, since the RAG knowledge base is breed-specific.
        default_breed = getattr(selected_pet, "species", "") or ""
        ai_breed = st.text_input(
            "Breed (optional — improves the plan; defaults to species)",
            value=default_breed,
            key="ai_breed_input",
        )
    with col_b:
        ai_weight = st.number_input(
            "Weight (kg, optional)",
            min_value=0.0, max_value=120.0, value=0.0, step=0.5,
            key="ai_weight_input",
        )

    ai_health_raw = st.text_input(
        "Health conditions (comma-separated, optional)",
        value="",
        placeholder="e.g. arthritis, allergies",
        key="ai_health_input",
    )

    ai_request = st.text_area(
        "Request",
        value="Create a daily care plan for tomorrow",
        height=80,
        key="ai_request_input",
    )

    if st.button("Generate AI Care Plan", key="generate_ai_plan_button"):
        if selected_pet is None:
            st.error("Selected pet not found.")
        else:
            # Build the pet_profile dict the agent expects.
            health_conditions_list = [
                c.strip() for c in ai_health_raw.split(",") if c.strip()
            ]
            pet_profile = {
                "name": selected_pet.name,
                "breed": ai_breed.strip()
                or getattr(selected_pet, "species", None)
                or "Unknown",
                "age": selected_pet.age,
                "weight_kg": ai_weight,
                "health_conditions": health_conditions_list,
            }

            try:
                agent = _get_pawpal_agent()
                with st.spinner("Generating AI care plan..."):
                    result = agent.run(pet_profile, ai_request)

                st.subheader("📋 AI Care Plan")
                st.markdown(result.get("validated_plan", "_(no plan generated)_"))

                st.subheader("📊 Confidence & Issues")
                confidence = float(result.get("confidence_score", 0.0))
                st.write(f"**Confidence:** {confidence:.2f}")
                st.progress(min(max(confidence, 0.0), 1.0))
                issues = result.get("issues", [])
                if issues:
                    st.markdown("**Issues:**")
                    for issue in issues:
                        st.markdown(f"- ⚠️ {issue}")
                else:
                    st.success("No issues — plan covers all required elements.")

                st.subheader("🧩 Explanation")
                st.markdown(result.get("explanation", "_(no explanation generated)_"))

            except Exception as e:
                # Graceful failure — friendly message for the user, details to console.
                print(f"[PawPal+] AI care plan error: {e!r}")
                st.error(
                    "Could not generate the AI care plan. Check that GROQ_API_KEY "
                    "is set in your .env file, then try again.\n\n"
                    f"Details: {e}"
                )

st.divider()
st.caption("🐾 PawPal+ — Powered by intelligent pet care scheduling")
