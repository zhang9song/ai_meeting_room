import gradio as gr
from datetime import datetime
from pathlib import Path
import yaml
import html
import base64
import json
import markdown2
from config import CONFIG_FILE, MEETINGS_DIR
from llm_loader import load_model_configs
from meeting_engine import MeetingEngine, Participant, Host, LLMClient, get_avatar_color, get_avatar_svg


def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_config(models_json, default_search):
    models = json.loads(models_json)
    config = {
        "llm_models": models,
        "default_participants": 3,
        "search_enabled": default_search,
        "max_rounds": 3
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
    return "配置已保存！"


def load_models_for_display():
    config = load_config()
    models = config.get("llm_models", [])
    return json.dumps(models, ensure_ascii=False, indent=2)


def load_default_search():
    config = load_config()
    return config.get("search_enabled", True)


def create_meeting(topic, participants_count, max_rounds, global_search, *participant_args):
    if not topic:
        gr.Warning("请输入会议议题")
        return [], "请输入议题", ""

    count = int(participants_count)
    args = list(participant_args)

    participant_details = []
    for i in range(count):
        name = args[i * 4]
        role = args[i * 4 + 1]
        role_desc = args[i * 4 + 2]
        model_name = args[i * 4 + 3]
        if not name:
            name = f"参会者{i + 1}"
        if not role:
            role = f"角色{i + 1}"
        participant_details.append({
            "name": name,
            "role": role,
            "role_desc": role_desc or "",
            "model_name": model_name
        })

    model_configs = load_model_configs()
    model_map = {m["name"]: m for m in model_configs}

    if len(model_configs) == 0:
        gr.Warning("请在系统配置页面配置至少一个LLM模型")
        return [], "请配置模型", ""

    participants = []
    for pd in participant_details:
        mc = model_map.get(pd["model_name"], model_configs[0])
        llm_client = LLMClient(
            name=mc["name"],
            base_url=mc["base_url"],
            api_key=mc["api_key"],
            model=mc["model"]
        )
        participant = Participant(
            name=pd["name"],
            role=pd["role"],
            role_description=pd["role_desc"],
            llm_client=llm_client,
            enable_search=global_search
        )
        participants.append(participant)

    host_model_config = model_configs[0]
    host_llm = LLMClient(
        name=host_model_config["name"],
        base_url=host_model_config["base_url"],
        api_key=host_model_config["api_key"],
        model=host_model_config["model"]
    )
    host = Host(host_llm)

    engine = MeetingEngine(
        participants=participants,
        host=host,
        topic=topic,
        max_rounds=int(max_rounds)
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_topic = "".join(c for c in topic if c.isalnum() or c in (" ", "-", "_")).rstrip()
    filename = MEETINGS_DIR / f"{timestamp}_{safe_topic}.md"

    status_text = "会议进行中..."

    for event_type, content in engine.run_meeting():
        if event_type == "status":
            status_text = content
            chat_html = render_chat_messages(engine.chat_messages)
            yield chat_html, status_text, ""
        elif event_type == "chat_update":
            chat_html = render_chat_messages(content)
            yield chat_html, status_text, ""
        elif event_type == "meeting_complete":
            chat_html = render_chat_messages(engine.chat_messages)
            engine.save_meeting_log(str(filename))
            yield chat_html, "会议已完成", str(filename)


MD_EXTRAS = ['fenced-code-blocks', 'tables', 'strike', 'underline', 'break-on-newline', 'cuddled-lists', 'header-ids', 'numbering']

def render_md(text: str) -> str:
    try:
        return markdown2.markdown(text, extras=MD_EXTRAS)
    except Exception:
        return html.escape(text).replace("\n", "<br>")

def render_chat_messages(messages: list) -> str:
    if not messages:
        return '''
        <div style="display:flex;align-items:center;justify-content:center;height:100%;color:#999;font-size:16px;">
            <div style="text-align:center;">
                <div style="font-size:48px;margin-bottom:16px;">🏛️</div>
                <div>会议尚未开始，请在左侧配置后点击"开始会议"</div>
            </div>
        </div>'''

    auto_scroll_id = f"chat_scroll_{datetime.now().timestamp()}"

    html_out = f'<div id="{auto_scroll_id}" class="chat-container" style="padding:16px;overflow-y:auto;flex:1;">'
    for msg in messages:
        is_host = msg.get("is_host", False)
        color = msg.get("avatar_color", "#888")
        avatar_svg = msg.get("avatar_svg", "")
        role_name = msg.get("role_name", msg.get("role", ""))
        content = msg.get("content", "")
        timestamp = msg.get("timestamp", "")

        avatar_html = f'<img src="data:image/svg+xml;base64,{b64(avatar_svg)}" style="width:36px;height:36px;border-radius:50%;flex-shrink:0;" />'
        rendered_content = render_md(content)

        if is_host:
            html_out += f'''
            <div style="display:flex;justify-content:flex-end;margin:16px 0 8px 0;">
                <div style="display:flex;flex-direction:row-reverse;align-items:flex-start;gap:8px;max-width:70%;">
                    <div>{avatar_html}</div>
                    <div style="min-width:0;text-align:right;">
                        <div style="font-size:11px;color:#aaa;margin-bottom:3px;display:flex;gap:8px;justify-content:flex-end;">
                            <span style="font-weight:500;">主持人</span>
                            <span>{timestamp}</span>
                        </div>
                        <div class="md-content md-host" style="background:#f5f5f5;border:1px solid #e0e0e0;border-radius:12px;border-top-right-radius:4px;padding:8px 14px;font-size:13px;color:#666;line-height:1.5;text-align:left;">
                            {rendered_content}
                        </div>
                    </div>
                </div>
            </div>'''
        else:
            html_out += f'''
            <div style="display:flex;justify-content:flex-start;margin:8px 0;">
                <div style="display:flex;gap:8px;max-width:80%;">
                    <div>{avatar_html}</div>
                    <div style="min-width:0;">
                        <div style="font-size:11px;color:#aaa;margin-bottom:3px;display:flex;gap:8px;">
                            <span style="font-weight:500;">{role_name}</span>
                            <span>{timestamp}</span>
                        </div>
                        <div class="md-content md-guest" style="background:#e8f4fd;border:1px solid #d0e3f0;border-radius:12px;border-top-left-radius:4px;padding:10px 14px;font-size:13px;line-height:1.6;color:#333;word-wrap:break-word;">
                            {rendered_content}
                        </div>
                    </div>
                </div>
            </div>'''

    html_out += '</div>'
    html_out += f'''
    <script>
    (function() {{
        var el = document.getElementById('{auto_scroll_id}');
        if (el) {{ el.scrollTop = el.scrollHeight; }}
    }})();
    </script>'''
    return html_out


def b64(s: str) -> str:
    return base64.b64encode(s.encode()).decode()


model_configs = load_model_configs()
model_names = [m["name"] for m in model_configs]


with gr.Blocks(title="AI会议室") as app:
    gr.Markdown("# 🏛️ AI会议室", elem_id="main-title")

    with gr.Tabs():
        with gr.Tab("会议室"):
            with gr.Row(equal_height=True):
                with gr.Column(scale=1, min_width=380):
                    with gr.Accordion("会议配置", open=True):
                        topic = gr.Textbox(label="会议议题", placeholder="请输入会议议题...", lines=2)
                        participants_count = gr.Slider(
                            minimum=2, maximum=5, value=3, step=1, label="参会人数"
                        )
                        max_rounds = gr.Slider(
                            minimum=1, maximum=5, value=2, step=1, label="讨论轮次"
                        )
                        global_search = gr.Checkbox(
                            label="启用在线搜索（参会者将使用网络搜索支持观点）",
                            value=True
                        )

                        participant_components = []
                        for i in range(5):
                            with gr.Group(visible=(i < 3)) as p_group:
                                gr.Markdown(f"##### 参会者 {i+1}")
                                with gr.Row():
                                    p_name = gr.Textbox(label="姓名", value=f"参会者{i+1}")
                                    p_role = gr.Textbox(label="角色", value=f"角色{i+1}")
                                    p_model = gr.Dropdown(choices=model_names, value=model_names[0] if model_names else None, label="LLM模型")
                                p_role_desc = gr.Textbox(label="角色说明", value="", placeholder="可选，描述该角色的背景和专业方向")
                                participant_components.append((p_group, p_name, p_role, p_role_desc, p_model))

                        start_btn = gr.Button("🚀 开始会议", variant="primary", size="lg")

                with gr.Column(scale=3):
                    status_bar = gr.Markdown("### 状态：等待开始会议")
                    chat_output = gr.HTML(
                        value='''
                        <div style="display:flex;align-items:center;justify-content:center;height:100%;color:#999;font-size:16px;">
                            <div style="text-align:center;">
                                <div style="font-size:48px;margin-bottom:16px;">🏛️</div>
                                <div>会议尚未开始，请在左侧配置后点击"开始会议"</div>
                            </div>
                        </div>''',
                        elem_id="chat-area"
                    )
                    file_output = gr.Textbox(label="会议记录文件路径", visible=False)

        with gr.Tab("系统配置"):
            gr.Markdown("## 大模型配置")
            gr.Markdown("在此配置可用的LLM模型，所有参会者将从以下模型中选择。")

            models_json_input = gr.Textbox(
                label="模型配置 (JSON格式)",
                value=load_models_for_display,
                lines=15,
                max_lines=30
            )
            gr.Markdown("""
            **JSON格式示例：**
            ```json
            [
              {
                "name": "copaw-flash-9b",
                "base_url": "http://127.0.0.1:1234/v1",
                "api_key": "your-api-key",
                "model": "copaw-flash-9b"
              }
            ]
            ```
            """)

            default_search = gr.Checkbox(
                label="默认启用在线搜索",
                value=load_default_search,
                info="启用后，所有参会者在发言时会自动进行网络搜索以获取参考资料"
            )

            with gr.Row():
                save_btn = gr.Button("💾 保存配置", variant="primary")
                reload_btn = gr.Button("🔄 重新加载配置")

            save_status = gr.Textbox(label="保存状态", interactive=False)

            def handle_save(models_json, search_val):
                return save_config(models_json, search_val)

            def handle_reload():
                return load_models_for_display()

            save_btn.click(
                fn=handle_save,
                inputs=[models_json_input, default_search],
                outputs=[save_status]
            )

            reload_btn.click(
                fn=handle_reload,
                outputs=[models_json_input]
            )

    all_inputs = [topic, participants_count, max_rounds, global_search]
    for _, p_name, p_role, p_role_desc, p_model in participant_components:
        all_inputs.extend([p_name, p_role, p_role_desc, p_model])

    start_btn.click(
        fn=create_meeting,
        inputs=all_inputs,
        outputs=[chat_output, status_bar, file_output]
    )

    def update_visibility(count):
        count = int(count)
        updates = []
        for i in range(5):
            updates.append(gr.Row(visible=(i < count)))
        return updates

    participants_count.change(
        fn=update_visibility,
        inputs=[participants_count],
        outputs=[p_group for p_group, _, _, _, _ in participant_components]
    )


if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=7860, share=False)
