import gradio as gr
from utils.chat_util import chat_response, summarize_document


# Modernized CSS for a sleek, premium look
custom_css = """
/* 1. Overall App Background & Font */
.gradio-container {
    background-color: #f8fafc !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* 2. Container Shadow & Rounding */
#chatbot {
    border: none !important;
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1) !important;
    border-radius: 12px !important;
    background: white !important;
}

/* 3. User Bubble (Question) - Modern Asymmetrical Corners */
.message.user {
    background: #87CEEB !important;
    color: #000000 !important;
    border-radius: 18px 18px 2px 18px !important; /* Sharp corner on bottom-right */
    padding: 12px 16px !important;
    margin-bottom: 10px !important;
    box-shadow: 0 4px 6px -1px rgba(0, 122, 255, 0.2) !important;
}

/* 4. Bot Bubble (Answer) - Soft Neutral Look */
.message.bot {
    background-color: #f1f5f9 !important;
    color: #000000 !important;
    border-radius: 18px 18px 18px 2px !important; /* Sharp corner on bottom-left */
    padding: 12px 16px !important;
    border: 1px solid #e2e8f0 !important;
    margin-bottom: 10px !important;
}

/* 5. Smooth Scrollbar */
#chatbot .message-wrap::-webkit-scrollbar {
    width: 6px;
}
#chatbot .message-wrap::-webkit-scrollbar-thumb {
    background-color: #cbd5e1;
    border-radius: 10px;
}
"""

# Integrate into your existing code
with gr.Blocks(css=custom_css) as chatInterface:
    gr.Markdown("# 📄 PromptDoc AI")
    
    with gr.Row():
        with gr.Column(scale=1):
            file_input = gr.File(label="Upload PDF or TXT")
            upload_btn = gr.Button("Process & Summarize", variant="primary")
            summary_output = gr.Markdown(label="Document Summary")
            
        with gr.Column(scale=2):
            # Pass the ID "chatbot" to the inner chatbot component
            chatbot_component = gr.Chatbot(elem_id="chatbot")
            msg_input = gr.Textbox(
                placeholder="Ask a question about your document...",
                label="Your Question",
                interactive=False
            )
            submit_btn = gr.Button("Send", variant="primary", interactive=False)
    
    # State to track if summary is loaded
    summary_loaded = gr.State(False)
    
    def process_and_summarize(file):
        """Process document and enable chat after summary loads"""
        # Show processing state
        yield "", gr.update(interactive=False), gr.update(interactive=False), gr.update(value="Processing...", interactive=False)
        
        # Stream the summary
        for summary in summarize_document(file):
            yield summary, gr.update(interactive=False), gr.update(interactive=False), gr.update(value="Processing...", interactive=False)
        
        # After summary is complete, enable chat and reset button
        yield summary, gr.update(interactive=True, placeholder="Ask a question about your document..."), gr.update(interactive=True), gr.update(value="Process & Summarize", interactive=True)
    
    def send_message(message, history):
        """Handle chat messages with streaming"""
        if not message.strip():
            return history, ""
        
        # Initialize history if None
        if history is None:
            history = []
        
        # Add user message to history in proper format
        history = history + [{"role": "user", "content": message}]
        yield history, ""
        
        # Add placeholder for bot response
        history = history + [{"role": "assistant", "content": ""}]
        
        # Convert history to format expected by chat_response (list of tuples)
        tuple_history = []
        for i in range(0, len(history) - 1, 2):
            if i + 1 < len(history):
                tuple_history.append((history[i]["content"], history[i + 1]["content"]))
        
        # Stream bot response
        for response in chat_response(message, tuple_history):
            history[-1]["content"] = response
            yield history, ""
        
        return history, ""
    
    # Connect the upload button with loading state
    upload_btn.click(
        fn=process_and_summarize,
        inputs=[file_input],
        outputs=[summary_output, msg_input, submit_btn, upload_btn]
    )
    
    # Handle message submission
    submit_btn.click(
        fn=send_message,
        inputs=[msg_input, chatbot_component],
        outputs=[chatbot_component, msg_input]
    )
    
    msg_input.submit(
        fn=send_message,
        inputs=[msg_input, chatbot_component],
        outputs=[chatbot_component, msg_input]
    )
    
    # Clear chatbot when new file is uploaded
    file_input.change(lambda: None, outputs=[chatbot_component])