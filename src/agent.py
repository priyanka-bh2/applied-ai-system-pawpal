"""
Agentic Planning Module for PawPal+
Uses LangGraph to create multi-step pet care planning workflows.
"""

import os
from dotenv import load_dotenv
from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from .retriever import CareGuidelineRetriever

load_dotenv()

class AgentState(TypedDict):
    """State schema for the planning agent"""
    pet_profile: dict
    user_request: str
    retrieved_context: List[str]
    draft_plan: str
    validated_plan: str
    confidence_score: float
    explanation: str
    issues: List[str]

class PawPalAgent:
    """AI Agent for generating personalized pet care plans"""
    
    def __init__(self):
        """Initialize agent with LLM, retriever, and graph"""
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            api_key=os.getenv("GROQ_API_KEY")
        )
        self.retriever = CareGuidelineRetriever()
        self.graph = self._build_graph()
    
    def _retrieve_context(self, state: AgentState) -> AgentState:
        """Retrieve relevant breed-specific care guidelines"""
        breed = state['pet_profile'].get('breed', '')
        age = state['pet_profile'].get('age', '')
        query = f"{breed} {age} year old care guidelines exercise diet"
        state['retrieved_context'] = self.retriever.retrieve(query, k=2)
        return state
    
    def _generate_plan(self, state: AgentState) -> AgentState:
        """Generate a draft care plan using retrieved context"""
        pet = state['pet_profile']
        context = "\n\n".join(state['retrieved_context']) if state['retrieved_context'] else "No specific guidelines retrieved."
        
        prompt = f"""
You are a professional pet care planner. Generate a detailed daily care plan.

Pet Information:
- Name: {pet.get('name', 'Unknown')}
- Breed: {pet.get('breed', 'Unknown')}
- Age: {pet.get('age', 'Unknown')} years
- Weight: {pet.get('weight_kg', 'Unknown')} kg
- Health Conditions: {', '.join(pet.get('health_conditions', ['None'])) or 'None'}

Retrieved Care Guidelines:
{context}

User Request: {state['user_request']}

Generate a structured daily care plan with:
1. Feeding schedule (times, portions)
2. Hydration (always include a fresh water recommendation - access, refresh frequency, and approximate daily intake)
3. Exercise activities (duration, type)
4. Grooming needs
5. Health monitoring (if applicable)
6. Mental stimulation activities

Always include a dedicated hydration/water recommendation - never omit it, even if the retrieved guidelines do not mention water.
Be specific and cite the guidelines where relevant.
"""
        response = self.llm.invoke(prompt)
        state['draft_plan'] = response.content
        return state
    
    def _validate_plan(self, state: AgentState) -> AgentState:
        """Validate the plan for safety and completeness"""
        issues = []
        confidence = 1.0
        
        # Check for missing context
        if not state['retrieved_context']:
            issues.append("No breed-specific guidelines retrieved - recommendations are general")
            confidence -= 0.3
        
        # Check for health conditions
        if state['pet_profile'].get('health_conditions'):
            if "veterinarian" not in state['draft_plan'].lower() and "vet" not in state['draft_plan'].lower():
                issues.append("Health conditions present but no vet consultation mentioned")
                confidence -= 0.15
        
        # Check plan completeness
        plan_lower = state['draft_plan'].lower()
        required_elements = ['feeding', 'exercise', 'water']
        for element in required_elements:
            if element not in plan_lower:
                issues.append(f"Missing {element} recommendation")
                confidence -= 0.1
        
        state['issues'] = issues
        state['confidence_score'] = max(confidence, 0.0)
        state['validated_plan'] = state['draft_plan']
        
        return state
    
    def _generate_explanation(self, state: AgentState) -> AgentState:
        """Generate explanation of why each task is important"""
        prompt = f"""
Explain WHY each task in this care plan is important for this specific pet:

Pet: {state['pet_profile']['breed']}, {state['pet_profile']['age']} years old

Care Plan:
{state['validated_plan']}

Retrieved Guidelines Used:
{state['retrieved_context']}

For each major task, explain:
1. Why it's important for this breed/age
2. What happens if this need is not met
3. Cite specific guidelines from the context

Keep explanation concise (150-200 words).
"""
        response = self.llm.invoke(prompt)
        state['explanation'] = response.content
        return state
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(AgentState)
        
        workflow.add_node("retrieve", self._retrieve_context)
        workflow.add_node("plan", self._generate_plan)
        workflow.add_node("validate", self._validate_plan)
        workflow.add_node("explain", self._generate_explanation)
        
        workflow.set_entry_point("retrieve")
        workflow.add_edge("retrieve", "plan")
        workflow.add_edge("plan", "validate")
        workflow.add_edge("validate", "explain")
        workflow.add_edge("explain", END)
        
        return workflow.compile()
    
    def run(self, pet_profile: dict, user_request: str) -> AgentState:
        """Run the complete planning workflow"""
        initial_state = {
            "pet_profile": pet_profile,
            "user_request": user_request,
            "retrieved_context": [],
            "draft_plan": "",
            "validated_plan": "",
            "confidence_score": 0.0,
            "explanation": "",
            "issues": []
        }
        
        final_state = self.graph.invoke(initial_state)
        return final_state