interface Message {
  role: "user" | "assistant" | "system";
  content: string;
}

interface Props {
  messages: Message[];
}

export default function ChatWindow({ messages }: Props) {
  return (
    <div className="flex flex-col gap-3 p-4">
      {messages.map((msg, i) => (
        <div
          key={i}
          className={`rounded-lg px-4 py-3 text-sm max-w-[80%] ${
            msg.role === "user"
              ? "bg-blue-600 text-white self-end"
              : msg.role === "system"
                ? "bg-gray-100 text-gray-500 self-center text-center text-xs"
                : "bg-white border border-gray-200 text-gray-800 self-start"
          }`}
        >
          {msg.content}
        </div>
      ))}
    </div>
  );
}
