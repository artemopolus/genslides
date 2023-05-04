import gradio as gr

def greet(name):
    return "Hello " + name + "!"

def set_image(name):
    return "img/g1.png"

with gr.Blocks() as demo:
    init = gr.Textbox(label="Init",lines=4)
    name = gr.Textbox(label="Name",lines=4)
    endi = gr.Textbox(label="Endi",lines=4)
    question = gr.Textbox(label="Question",lines=4)
    search = gr.Textbox(label="Search",lines=4)
    userinput = gr.Textbox(label="User Input",lines=4)
    output = gr.Textbox(label="Output Box")
    greet_btn = gr.Button("Greet")
    greet_btn.click(fn=greet, inputs=name, outputs=output, api_name="greet")
    image = gr.Image()
    img_btn = gr.Button("Img")
    img_btn.click(fn=set_image,inputs=name, outputs=image)


demo.launch(server_port=8888)

