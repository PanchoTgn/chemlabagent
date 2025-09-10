import streamlit as st
import openai
from dotenv import load_dotenv
import os
import json

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Question bank - now with Socratic progression
TOPICS = [
    {
        "topic": "Adiabatic Calorimetry",
        "initial_question": "Imagine you're doing a reaction in a calorimeter. What do you think 'adiabatic' means, and why is this important for measuring heat changes?",
        "key_concepts": ["no heat exchange", "isolated system", "temperature change reflects heat of reaction"],
        "follow_ups": [
            "What would happen to our measurements if heat could escape to the surroundings?",
            "If a reaction releases heat but the calorimeter isn't perfectly adiabatic, would we measure more or less heat than the actual value?"
        ]
    },
    {
        "topic": "Exothermic Reactions and Temperature",
        "initial_question": "When you mix sodium hydroxide and hydrochloric acid, the solution gets warm. Walk me through what's happening at the molecular level that causes this temperature change.",
        "key_concepts": ["exothermic reaction", "energy release", "heat increases temperature", "bond formation releases energy"],
        "follow_ups": [
            "Where does this energy actually come from?",
            "Why does releasing energy make the solution feel warm to touch?"
        ]
    },
    {
        "topic": "Water Equivalent of Calorimeter",
        "initial_question": "The calorimeter itself also heats up during the reaction. We account for this using something called 'water equivalent' (10g for your calorimeters). What do you think this concept means?",
        "key_concepts": ["calorimeter absorbs heat", "equivalent mass of water", "heat capacity"],
        "follow_ups": [
            "Why do we use water as our reference?",
            "How would ignoring the calorimeter's heat absorption affect our calculations?"
        ]
    },
    {
        "topic": "Limiting Reagent and Stoichiometry",
        "initial_question": "You're mixing 100 mL of 0.5 M NaOH with 5 mL of concentrated HCl (37% w/w, density 1.19 g/mL). Before doing any calculations, which reagent do you think might be limiting and why?",
        "key_concepts": ["limiting reagent", "stoichiometry", "mole calculations", "HCl is limiting"],
        "follow_ups": [
            "Let's calculate the actual moles - how many moles of NaOH do you have?",
            "Now for HCl - can you calculate the moles of HCl in 5 mL of 37% solution?"
        ]
    },
    {
        "topic": "Heat of Dilution vs. Heat of Neutralization",
        "initial_question": "In this experiment, we measure the heat of HCl dilution separately from the neutralization. Why do you think we need to separate these two heat effects?",
        "key_concepts": ["dilution releases heat", "separate processes", "concentrated acid dilution", "total heat vs reaction heat"],
        "follow_ups": [
            "What happens when you add water to concentrated acid?",
            "Why don't we worry about the heat of dilution for the already-dilute NaOH solution?"
        ]
    }
]

def get_ai_response(conversation_history, student_response, topic_data):
    """Get Socratic response from AI"""
    try:
        client = openai.OpenAI()
        
        # Build the conversation context
        system_prompt = f"""You are a supportive chemistry tutor using the Socratic method. 

Topic: {topic_data['topic']}
Key concepts to eventually cover: {', '.join(topic_data['key_concepts'])}

Your approach:
1. ALWAYS start with positive reinforcement - acknowledge what the student got right
2. Use the student's answer as a building block - don't just correct, but guide discovery
3. Ask follow-up questions that help them think deeper
4. Be encouraging and build confidence
5. If they're struggling, break concepts into smaller pieces
6. If they're doing well, challenge them appropriately

Current conversation: {conversation_history}

Respond as a caring tutor who wants the student to discover the answer through guided questions."""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Student's response: {student_response}"}
            ],
            max_tokens=300,
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"I'm having trouble processing that right now. Can you try rephrasing your answer? (Error: {str(e)})"

def evaluate_topic_understanding(conversation_history, key_concepts):
    """Evaluate if student has grasped the key concepts"""
    try:
        client = openai.OpenAI()
        
        system_prompt = f"""Based on this conversation about chemistry, evaluate if the student demonstrates understanding of these key concepts: {', '.join(key_concepts)}

Rate as:
- STRONG: Clearly understands most/all key concepts
- DEVELOPING: Shows partial understanding, getting there
- NEEDS_WORK: Limited understanding, needs more guidance

Provide a brief explanation of your assessment."""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Conversation: {conversation_history}"}
            ],
            max_tokens=150,
            temperature=0.3
        )
        
        result = response.choices[0].message.content
        
        if "STRONG" in result.upper():
            return "STRONG", result
        elif "DEVELOPING" in result.upper():
            return "DEVELOPING", result
        else:
            return "NEEDS_WORK", result
            
    except Exception as e:
        return "ERROR", f"Assessment error: {str(e)}"

# Initialize session state
if 'current_topic' not in st.session_state:
    st.session_state.current_topic = 0
if 'conversations' not in st.session_state:
    st.session_state.conversations = {}
if 'student_name' not in st.session_state:
    st.session_state.student_name = ""
if 'assessment_started' not in st.session_state:
    st.session_state.assessment_started = False
if 'topic_completed' not in st.session_state:
    st.session_state.topic_completed = False

# Streamlit App
st.title("🧪 Chemistry Lab Learning Assistant")
st.subheader("Calorimetry Lab - Let's explore the concepts together!")

# Get student name
if not st.session_state.student_name:
    name = st.text_input("What's your name?")
    if st.button("Let's Start Learning!"):
        if name.strip():
            st.session_state.student_name = name.strip()
            st.session_state.assessment_started = True
            st.rerun()
        else:
            st.error("Please enter your name first.")

elif st.session_state.assessment_started:
    current_topic_idx = st.session_state.current_topic
    
    # Check if we've completed all topics
    if current_topic_idx >= len(TOPICS):
        # Show final results
        st.success("🎉 Great job completing the learning session!")
        
        st.write(f"**Learning Summary for {st.session_state.student_name}:**")
        
        strong_topics = []
        developing_topics = []
        needs_work_topics = []
        
        for i, topic in enumerate(TOPICS):
            if i in st.session_state.conversations:
                conversation = st.session_state.conversations[i]
                if conversation.get('final_assessment'):
                    level = conversation['final_assessment'][0]
                    if level == 'STRONG':
                        strong_topics.append(topic['topic'])
                    elif level == 'DEVELOPING':
                        developing_topics.append(topic['topic'])
                    else:
                        needs_work_topics.append(topic['topic'])
        
        if strong_topics:
            st.success("🌟 **Strong Understanding:**")
            for topic in strong_topics:
                st.write(f"- {topic}")
        
        if developing_topics:
            st.info("📈 **Developing Understanding:**")
            for topic in developing_topics:
                st.write(f"- {topic}")
        
        if needs_work_topics:
            st.warning("📚 **Areas for Review:**")
            for topic in needs_work_topics:
                st.write(f"- {topic}")
        
        # Overall readiness
        total_topics = len([t for t in [strong_topics, developing_topics] if t])
        ready = len(strong_topics) >= len(TOPICS) * 0.6  # 60% strong understanding
        
        if ready:
            st.success(f"✅ {st.session_state.student_name} shows good readiness for the lab!")
        else:
            st.info(f"📖 {st.session_state.student_name} would benefit from reviewing some concepts before lab.")
        
        if st.button("Start Over"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
            
    else:
        # Current topic
        current_topic = TOPICS[current_topic_idx]
        
        st.write(f"**Topic {current_topic_idx + 1} of {len(TOPICS)}: {current_topic['topic']}**")
        
        # Initialize conversation for this topic
        if current_topic_idx not in st.session_state.conversations:
            st.session_state.conversations[current_topic_idx] = {
                'messages': [],
                'completed': False
            }
        
        conversation = st.session_state.conversations[current_topic_idx]
        
        # Show conversation history
        for msg in conversation['messages']:
            if msg['role'] == 'assistant':
                st.info(f"🧑‍🏫 **Tutor:** {msg['content']}")
            else:
                st.write(f"👤 **You:** {msg['content']}")
        
        # Show initial question if no conversation yet
        if not conversation['messages']:
            st.info(f"🧑‍🏫 **Tutor:** {current_topic['initial_question']}")
        
        # Student input
        if not conversation['completed']:
            # Create a unique key that changes after each response to clear the text area
            input_key = f"input_{current_topic_idx}_{len(conversation['messages'])}"
            student_input = st.text_area("Your response:", key=input_key, height=100)
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Send Response", key=f"send_{current_topic_idx}"):
                    if student_input.strip():
                        # Add student message
                        conversation['messages'].append({
                            'role': 'user',
                            'content': student_input
                        })
                        
                        # Get AI response
                        conversation_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation['messages']])
                        
                        with st.spinner("Thinking about your response..."):
                            ai_response = get_ai_response(conversation_text, student_input, current_topic)
                        
                        # Add AI response
                        conversation['messages'].append({
                            'role': 'assistant', 
                            'content': ai_response
                        })
                        
                        st.rerun()
                    else:
                        st.error("Please provide a response.")
            
            with col2:
                # Allow moving to next topic after some interaction
                if len(conversation['messages']) >= 4:  # At least 2 exchanges
                    if st.button("I understand this topic", key=f"next_{current_topic_idx}"):
                        # Final assessment
                        conversation_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation['messages']])
                        
                        with st.spinner("Assessing your understanding..."):
                            assessment = evaluate_topic_understanding(conversation_text, current_topic['key_concepts'])
                        
                        conversation['final_assessment'] = assessment
                        conversation['completed'] = True
                        
                        # Show assessment
                        level, explanation = assessment
                        if level == 'STRONG':
                            st.success(f"🌟 {explanation}")
                        elif level == 'DEVELOPING':
                            st.info(f"📈 {explanation}")
                        else:
                            st.warning(f"📚 {explanation}")
                        
                        st.session_state.current_topic += 1
                        st.rerun()
        
        else:
            # Topic completed, show next button
            if st.button("Continue to Next Topic", key=f"continue_{current_topic_idx}"):
                st.session_state.current_topic += 1
                st.rerun()