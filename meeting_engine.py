from llm_client import LLMClient
from searcher import WebSearcher
from datetime import datetime
from typing import Optional, Generator, Callable

AVATAR_COLORS = [
    "#4A90D9", "#E74C3C", "#2ECC71", "#F39C12",
    "#9B59B6", "#1ABC9C", "#E67E22", "#3498DB",
    "#8E44AD", "#D35400", "#16A085", "#2980B9",
]


def get_avatar_color(name: str) -> str:
    return AVATAR_COLORS[hash(name) % len(AVATAR_COLORS)]


def get_avatar_svg(name: str, color: str) -> str:
    initial = name[0].upper() if name else "?"
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40"><circle cx="20" cy="20" r="20" fill="{color}"/><text x="50%" y="50%" dominant-baseline="central" text-anchor="middle" fill="white" font-size="20" font-family="Arial">{initial}</text></svg>'
    return svg


class Participant:
    def __init__(self, name: str, role: str, role_description: str,
                 llm_client: LLMClient, enable_search: bool = True):
        self.name = name
        self.role = role
        self.role_description = role_description
        self.llm_client = llm_client
        self.enable_search = enable_search
        self.searcher = WebSearcher() if enable_search else None
        self.messages = []
        self.avatar_color = get_avatar_color(name)

    def get_system_prompt(self, topic: str) -> str:
        desc = f"。你的角色背景：{self.role_description}" if self.role_description else ""
        return f"""你是{self.name}，角色是{self.role}{desc}。你正在参加一个关于"{topic}"的AI会议。

你的职责：
1. 针对议题进行分析和表达看法
2. 对其他参会者的发言进行讨论，包括优缺点、合理性、合规性等
3. 可以使用在线搜索来支持你的观点
4. 最终目标是达成各方都比较认可的结论

请保持专业、客观，并积极参与讨论。"""

    def _build_speak_message(self, topic: str, previous_speeches: Optional[str]) -> str:
        if previous_speeches:
            return f"""请针对议题"{topic}"发表你的看法和分析。
            
其他参会者的发言如下，请参考他们的观点并发表你的见解：
{previous_speeches}

请发表你的观点："""
        else:
            return f"""请针对议题"{topic}"发表你的看法和分析。

请发表你的观点："""

    def _build_discuss_message(self, topic: str, all_speeches: str) -> str:
        return f"""请对其他参会者的发言进行讨论，分析其优缺点、合理性、合规性等。

之前的发言记录：
{all_speeches}

请发表你的讨论意见："""

    def search_and_speak(self, topic: str, previous_speeches: Optional[str] = None) -> str:
        if self.enable_search and self.searcher:
            search_query = f"{topic} 分析 观点"
            search_results = self.searcher.search(search_query)
            search_context = self.searcher.format_results(search_results)
            system_prompt = self.get_system_prompt(topic) + f"""

以下是在线搜索的结果，你可以参考这些资料来支持你的观点：
{search_context}"""
        else:
            system_prompt = self.get_system_prompt(topic)

        user_message = self._build_speak_message(topic, previous_speeches)
        self.messages.append({"role": "user", "content": user_message})
        response = self.llm_client.chat(self.messages, system_prompt)
        self.messages.append({"role": "assistant", "content": response})
        return response

    def search_and_speak_stream(self, topic: str, previous_speeches: Optional[str] = None) -> Generator[str, None, str]:
        if self.enable_search and self.searcher:
            search_query = f"{topic} 分析 观点"
            search_results = self.searcher.search(search_query)
            search_context = self.searcher.format_results(search_results)
            system_prompt = self.get_system_prompt(topic) + f"""

以下是在线搜索的结果，你可以参考这些资料来支持你的观点：
{search_context}"""
        else:
            system_prompt = self.get_system_prompt(topic)

        user_message = self._build_speak_message(topic, previous_speeches)
        self.messages.append({"role": "user", "content": user_message})

        full_response = ""
        for accumulated, delta in self.llm_client.chat_stream(self.messages, system_prompt):
            full_response = accumulated
            yield accumulated

        self.messages.append({"role": "assistant", "content": full_response})
        return full_response

    def search_and_discuss(self, topic: str, all_speeches: str) -> str:
        if self.enable_search and self.searcher:
            search_query = f"{topic} 讨论 优缺点"
            search_results = self.searcher.search(search_query)
            search_context = self.searcher.format_results(search_results)
            system_prompt = self.get_system_prompt(topic) + f"""

以下是在线搜索的结果，你可以参考这些资料来支持你的观点：
{search_context}"""
        else:
            system_prompt = self.get_system_prompt(topic)

        user_message = self._build_discuss_message(topic, all_speeches)
        self.messages.append({"role": "user", "content": user_message})
        response = self.llm_client.chat(self.messages, system_prompt)
        self.messages.append({"role": "assistant", "content": response})
        return response

    def search_and_discuss_stream(self, topic: str, all_speeches: str) -> Generator[str, None, str]:
        if self.enable_search and self.searcher:
            search_query = f"{topic} 讨论 优缺点"
            search_results = self.searcher.search(search_query)
            search_context = self.searcher.format_results(search_results)
            system_prompt = self.get_system_prompt(topic) + f"""

以下是在线搜索的结果，你可以参考这些资料来支持你的观点：
{search_context}"""
        else:
            system_prompt = self.get_system_prompt(topic)

        user_message = self._build_discuss_message(topic, all_speeches)
        self.messages.append({"role": "user", "content": user_message})

        full_response = ""
        for accumulated, delta in self.llm_client.chat_stream(self.messages, system_prompt):
            full_response = accumulated
            yield accumulated

        self.messages.append({"role": "assistant", "content": full_response})
        return full_response


class Host:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.messages = []

    def get_system_prompt(self, topic: str) -> str:
        return f"""你是会议主持人，负责关于"{topic}"的会议。

你的职责：
1. 维持会议秩序和流程
2. 记录和整理参会人发言
3. 不要发表自己对议题的看法
4. 引导讨论朝着达成共识的方向进行
5. 最终整理会议结论

请保持客观、公正，确保会议有序进行。"""

    def start_meeting(self, topic: str) -> str:
        system_prompt = self.get_system_prompt(topic)
        user_message = f"""会议现在开始。请宣布会议议题"{topic}"，并说明会议流程：
1. 首先请各位参会者依次发表对议题的看法
2. 然后进入讨论环节
3. 最终达成共识并总结

请宣布会议开始："""
        self.messages.append({"role": "user", "content": user_message})
        response = self.llm_client.chat(self.messages, system_prompt)
        self.messages.append({"role": "assistant", "content": response})
        return response

    def start_meeting_stream(self, topic: str) -> Generator[str, None, str]:
        system_prompt = self.get_system_prompt(topic)
        user_message = f"""会议现在开始。请宣布会议议题"{topic}"，并说明会议流程：
1. 首先请各位参会者依次发表对议题的看法
2. 然后进入讨论环节
3. 最终达成共识并总结

请宣布会议开始："""
        self.messages.append({"role": "user", "content": user_message})

        full_response = ""
        for accumulated, delta in self.llm_client.chat_stream(self.messages, system_prompt):
            full_response = accumulated
            yield accumulated

        self.messages.append({"role": "assistant", "content": full_response})
        return full_response

    def summarize(self, topic: str, all_speeches: str) -> str:
        system_prompt = self.get_system_prompt(topic)
        user_message = f"""请根据以下会议发言记录，总结各方观点，并整理出一个各方都比较认可的结论。

会议议题：{topic}

发言记录：
{all_speeches}

请总结会议内容并得出结论："""
        self.messages.append({"role": "user", "content": user_message})
        response = self.llm_client.chat(self.messages, system_prompt)
        self.messages.append({"role": "assistant", "content": response})
        return response

    def summarize_stream(self, topic: str, all_speeches: str) -> Generator[str, None, str]:
        system_prompt = self.get_system_prompt(topic)
        user_message = f"""请根据以下会议发言记录，总结各方观点，并整理出一个各方都比较认可的结论。

会议议题：{topic}

发言记录：
{all_speeches}

请总结会议内容并得出结论："""
        self.messages.append({"role": "user", "content": user_message})

        full_response = ""
        for accumulated, delta in self.llm_client.chat_stream(self.messages, system_prompt):
            full_response = accumulated
            yield accumulated

        self.messages.append({"role": "assistant", "content": full_response})
        return full_response


class MeetingEngine:
    def __init__(self, participants: list[Participant], host: Host, topic: str, max_rounds: int = 3):
        self.participants = participants
        self.host = host
        self.topic = topic
        self.max_rounds = max_rounds
        self.meeting_log = []
        self.current_round = 0
        self.chat_messages = []

    def log_event(self, speaker: str, content: str):
        self.meeting_log.append({
            "speaker": speaker,
            "content": content,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })

    def add_chat_message(self, speaker: str, content: str, is_host: bool = False, role_name: str = ""):
        color = "#888888" if is_host else get_avatar_color(speaker)
        avatar_svg = get_avatar_svg(speaker, color)
        self.chat_messages.append({
            "role": speaker,
            "role_name": role_name or speaker,
            "content": content,
            "is_host": is_host,
            "avatar_color": color,
            "avatar_svg": avatar_svg,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })

    def update_last_chat_message(self, content: str):
        if self.chat_messages:
            self.chat_messages[-1]["content"] = content

    def _stream_speaker(self, speaker_gen, speaker_name: str, is_host: bool = False, role_name: str = "") -> str:
        first = True
        full_response = ""
        for accumulated in speaker_gen:
            full_response = accumulated
            if first:
                self.add_chat_message(speaker_name, accumulated, is_host=is_host, role_name=role_name)
                first = False
            else:
                self.update_last_chat_message(accumulated)
            yield "chat_update", self.chat_messages.copy()
        return full_response

    def run_meeting(self, callback: Optional[Callable] = None) -> Generator[tuple, None, None]:
        self.current_round = 0
        self.chat_messages = []

        yield "status", f"主持人正在开场..."
        opening = ""
        for accumulated in self.host.start_meeting_stream(self.topic):
            opening = accumulated
            if not self.chat_messages or self.chat_messages[-1].get("role") != "主持人":
                self.add_chat_message("主持人", opening, is_host=True)
            else:
                self.update_last_chat_message(opening)
            yield "chat_update", self.chat_messages.copy()

        self.log_event("主持人", opening)
        if callback:
            callback("主持人", opening)

        full_speeches = opening + "\n\n"

        for round_num in range(1, self.max_rounds + 1):
            self.current_round = round_num

            if round_num == 1:
                yield "status", f"第{round_num}轮：依次发言中..."
                self.add_chat_message("主持人", f"--- 第{round_num}轮：各位依次发言 ---", is_host=True)
                yield "chat_update", self.chat_messages.copy()
                self.log_event("主持人", "请各位依次发表对议题的看法")

                for participant in self.participants:
                    yield "status", f"{participant.name} 正在发言..."
                    speech = ""
                    first_token = True
                    for accumulated in participant.search_and_speak_stream(self.topic, full_speeches):
                        speech = accumulated
                        if first_token:
                            self.add_chat_message(participant.name, speech, role_name=participant.role)
                            first_token = False
                        else:
                            self.update_last_chat_message(speech)
                        yield "chat_update", self.chat_messages.copy()

                    self.log_event(participant.name, speech)
                    if callback:
                        callback(participant.name, speech)
                    full_speeches += f"{participant.name} ({participant.role}): {speech}\n\n"
            else:
                yield "status", f"第{round_num}轮：讨论中..."
                self.add_chat_message("主持人", f"--- 第{round_num}轮：讨论环节 ---", is_host=True)
                yield "chat_update", self.chat_messages.copy()
                self.log_event("主持人", f"现在开始第{round_num}轮讨论")

                for participant in self.participants:
                    yield "status", f"{participant.name} 正在讨论..."
                    discussion = ""
                    first_token = True
                    for accumulated in participant.search_and_discuss_stream(self.topic, full_speeches):
                        discussion = accumulated
                        if first_token:
                            self.add_chat_message(participant.name, discussion, role_name=participant.role)
                            first_token = False
                        else:
                            self.update_last_chat_message(discussion)
                        yield "chat_update", self.chat_messages.copy()

                    self.log_event(participant.name, discussion)
                    if callback:
                        callback(participant.name, discussion)
                    full_speeches += f"{participant.name} ({participant.role}): {discussion}\n\n"

            self.add_chat_message("主持人", f"--- 第{round_num}轮结束 ---", is_host=True)
            yield "chat_update", self.chat_messages.copy()

        yield "status", "主持人正在总结..."
        self.add_chat_message("主持人", "--- 会议总结 ---", is_host=True)
        yield "chat_update", self.chat_messages.copy()

        summary = ""
        first_token = True
        for accumulated in self.host.summarize_stream(self.topic, full_speeches):
            summary = accumulated
            if first_token:
                self.add_chat_message("主持人", summary, is_host=True, role_name="总结")
                first_token = False
            else:
                self.update_last_chat_message(summary)
            yield "chat_update", self.chat_messages.copy()

        self.log_event("主持人", summary)
        if callback:
            callback("主持人", summary)

        self.add_chat_message("主持人", "会议结束。会议记录已保存。", is_host=True)
        yield "chat_update", self.chat_messages.copy()

        yield "meeting_complete", summary

    def get_meeting_log(self) -> str:
        log_text = "# 会议记录\n\n"
        log_text += f"**会议时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        log_text += f"**会议议题**: {self.topic}\n"
        log_text += f"**参会人员**: {', '.join([f'{p.name} ({p.role})' for p in self.participants])}\n"
        log_text += f"**主持人**: 主持人\n\n---\n\n"

        for entry in self.meeting_log:
            log_text += f"### [{entry['timestamp']}] {entry['speaker']}\n{entry['content']}\n\n---\n\n"

        return log_text

    def save_meeting_log(self, filename: str):
        log_content = self.get_meeting_log()
        with open(filename, "w", encoding="utf-8") as f:
            f.write(log_content)
        return filename
