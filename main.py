import gradio as gr
import matplotlib.pyplot as plt
from datetime import datetime

# Use Agg backend for Matplotlib to avoid GUI issues
import matplotlib
from openai import OpenAI
import requests

matplotlib.use('Agg')

# Set your OpenAI API key
api_key = ''

client = OpenAI(api_key=api_key)


tasks = []
completed_tasks = []


# DIY4Youth provides api for the k12 students to learn AI technology, please do not misuse it.

def call_api(diy4youth_student_api_key, prompt, system_content=None):
    """
    Calls the API at the specified URL and returns the data.

    Parameters:
    diy4youth_student_api_key (str): Student's access key for the diy4youth services.
    prompt (str): The user role's content.
    system_content (str): The system role's content if applicable, None otherwise.

    Returns:
    str: The data received from the API if successful, None otherwise.
    """
    try:
        if diy4youth_student_api_key and prompt:
            url = "https://www.diy4youth.org/ai/gpt"  # "http://127.0.0.1:5050/ai/gpt"  # fixed url for diy4youth students only

            data = {
                "diy4youth_student_api_key": diy4youth_student_api_key,
                "prompt": prompt,
                "system_content": system_content
            }

            response = requests.post(url, json=data)
            print("remote response", url, response)
            return response.json()
        else:
            print("Missing parameter")
            return None
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None


use_diy4youth_api = True

def chat_with_gpt3(prompt):
    if use_diy4youth_api:
        response = call_api("ONND-1-rerfe455", prompt, "You are a helpful assistant.")
        return str(response)

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ]
    )
    return response.choices[0].message.content.strip()


def add_task(task, due_date=None):
    if due_date:
        try:
            due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
        except ValueError:
            return "Invalid due date format. Please use YYYY-MM-DD."
        tasks.append({"task": task, "due_date": due_date})
        return f"Task '{task}' with due date {due_date} added to the checklist."
    else:
        tasks.append({"task": task, "due_date": None})
        return f"Task '{task}' added to the checklist."


def complete_task(task):
    task_to_remove = next((t for t in tasks if task in t["task"]), None)
    if task_to_remove:
        tasks.remove(task_to_remove)
        completed_tasks.append(task_to_remove)
        return f"Congratulations on finishing '{task}'! Nice job!"
    else:
        return f"Task '{task}' not found in the checklist."


def generate_pie_chart():
    total_tasks = len(tasks) + len(completed_tasks)
    if total_tasks == 0:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, 'No tasks to display', horizontalalignment='center', verticalalignment='center',
                transform=ax.transAxes, fontsize=15, color='red')
        plt.title("Task Completion Status")
        plt.savefig('pie_chart.png')
        plt.close(fig)
        return 'pie_chart.png'

    labels = ['Completed', 'Remaining']
    sizes = [len(completed_tasks), len(tasks)]
    colors = ['#4CAF50', '#FF6384']
    explode = (0.1, 0)  # explode the 1st slice (Completed)

    fig1, ax1 = plt.subplots()
    wedges, texts, autotexts = ax1.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%',
                                       shadow=True, startangle=140)
    ax1.axis('equal')
    plt.title(f"Task Completion Status\n{len(completed_tasks)} completed, {len(tasks)} remaining")

    for i, a in enumerate(autotexts):
        if sizes[i] > 0:
            a.set_text(f"{sizes[i]} ({a.get_text()})")

    plt.tight_layout()
    plt.savefig('pie_chart.png')
    plt.close(fig1)
    return 'pie_chart.png'


synonyms_for_add = ["add in ", "add on ", "add ", "create ", "insert ", "put ", "new "]

synonyms_for_end = ["finish ", "complete ", "done ", "end ", "stop ", "terminate ", "conclude ", "wrap up ", "close ", "finalize ",
                    "finished ", "completed ", "done ", "ended ", "stopped ", "terminated ", "concluded ", "wrapped up ", "closed ", "finalized "]
synonyms_for_end = synonyms_for_end + [f"i {synonym}" for synonym in synonyms_for_end] + [f"i have {synonym}" for synonym in synonyms_for_end] + [f"i've {synonym}" for synonym in synonyms_for_end] + [f"ive {synonym}" for synonym in synonyms_for_end] + [f"i'm {synonym}" for synonym in synonyms_for_end]  + [f"im {synonym}" for synonym in synonyms_for_end]
def process_input(user_input):
    if user_input == "placeholder_do_nothing": # internal use only
        return "Welcome to Study Planner! How can I help you today?"

    if any(user_input.lower().startswith(synonym) for synonym in synonyms_for_add): # adding study item
        item = [synonym for synonym in synonyms_for_add if user_input.lower().startswith(synonym)][0]
        parts = user_input[len(item):].split(" due ")
        task = parts[0]
        due_date = parts[1] if len(parts) > 1 else None
        return add_task(task, due_date)
    elif any(user_input.lower().startswith(synonym) for synonym in synonyms_for_end): # removing study item
        item = [synonym for synonym in synonyms_for_end if user_input.lower().startswith(synonym)][0]
        task = user_input[len(item):]
        return complete_task(task)
    elif user_input.lower().startswith("advice on "):
        subject = user_input[len("advice on "):].strip()
        advice_prompt = f"Can you provide some study advice for {subject}?"
        return chat_with_gpt3(advice_prompt)
    else:
        if len(tasks) != 0: str = f"Here are my tasks: {show_checklist()}\n User input: {user_input}"
        else: str = f"I currently have no tasks. {user_input}"
        return chat_with_gpt3(str)


def show_checklist():
    if len(tasks) == 0:
        return "No tasks here. Congratulations!"
    return "".join([f"{task['task']} (due {task['due_date']})\n" if task['due_date'] else f"{task['task']}\n" for task in tasks])

def show_completed_tasks():
    if len(completed_tasks) == 0:
        return "No tasks have been completed yet."
    return "".join([f"{task['task']} (due {task['due_date']})\n" if task['due_date'] else f"{task['task']}\n" for task in completed_tasks])

def interface(user_input):
    response = process_input(user_input)
    checklist = show_checklist()

    pie_chart = generate_pie_chart()
    return response, checklist, pie_chart, show_completed_tasks() # even if hardcode array, it doesn't work


def update_checklist():
    checklist = show_checklist()
    pie_chart = generate_pie_chart()
    return checklist, pie_chart


def mark_tasks_complete(completed_task_names):
    for task in completed_task_names:
        complete_task(task.split(" (due ")[0])  # Extract the task name without due date
    return update_checklist()


examples = [
    ["add Do math homework due 2024-06-01"],
    ["Completed Do math homework"],
    ["Advice on studying for history."],
    ["Add Write science report due 2024-06-10"],
    ["I have completed Write science report"],
    ["add Prepare for math test due 2024-06-15"],
]

# javascript copied from https://gradio.app/
js = """ 
function createGradioAnimation() {
    var container = document.createElement('div');
    container.id = 'gradio-animation';
    container.style.fontSize = '2em';
    container.style.fontWeight = 'bold';
    container.style.textAlign = 'center';
    container.style.marginBottom = '20px';

    var text = 'Welcome to Study Smart!';
    for (var i = 0; i < text.length; i++) {
        (function(i){
            setTimeout(function(){
                var letter = document.createElement('span');
                letter.style.opacity = '0';
                letter.style.transition = 'opacity 0.5s';
                letter.innerText = text[i];

                container.appendChild(letter);

                setTimeout(function() {
                    letter.style.opacity = '1';
                }, 50);
            }, i * 125);
        })(i);
    }

    var gradioContainer = document.querySelector('.gradio-container');
    gradioContainer.insertBefore(container, gradioContainer.firstChild);

    return 'Animation created';
}
"""
with gr.Blocks(theme=gr.themes.Soft(), css="gradio-app {background-color: #b6e8f3 !important;} .gradio-container {background-color: #beeaff} @keyframes levitate {   0%, 100% {     transform: translateY(0);   }   50% {     transform: translateY(-20px);   } } img[alt=\"logo\"] {   width: 120px;text-align: center; margin:0  auto; animation: levitate 3s ease-in-out infinite; }", js=js) as demo:
    gr.Markdown("""
    ![logo](https://media.discordapp.net/attachments/327932925243031562/1241970638415990834/wGjmPggnaltrgAAAABJRU5ErkJggg.png?ex=664c22ca&is=664ad14a&hm=62222d94fd7d06c068ebcff4f01966aa405b899f322cab6c6cb4fac925a8e15f)

    ## **Authors:** Fiona Yan
    
    
    Feeling *overwhelmed* with your tasks? Let me help you **manage your study schedule**!
    This is a study planner with chat, checklist, and progress tracking.
    
    ---
    """)

    with gr.Row():
        user_input = gr.Textbox(placeholder="Type your request here...", label="User Input")
        response_output = gr.Markdown()
        pie_chart_output = gr.Image(label='Status')

    # load the checklist for the first time
    with gr.Row():
        check_list = gr.Textbox(placeholder=show_checklist(), label="Checklist")
        finished_check_list = gr.Textbox(placeholder=show_completed_tasks(), label="Finished Tasks:")

    # load the checklist for the first time
    gr.update("")
    # make it load the actual checklist

    # checklist_output.change(fn=mark_tasks_complete, inputs=checklist_output, outputs=[checklist_output, pie_chart_output])
    user_input.submit(fn=interface, inputs=user_input, outputs=[response_output, check_list, pie_chart_output, finished_check_list])

    gr.Examples(examples, inputs=user_input)

    demo.load(fn=lambda: interface("placeholder_do_nothing"), inputs=None, outputs=[response_output, check_list, pie_chart_output, finished_check_list])


demo.launch(share=True)
