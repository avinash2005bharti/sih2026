const fs = require('fs');

const inputBarPath = 'FRONTEND/src/components/chat/ChatInputBar.jsx';
let content = fs.readFileSync(inputBarPath, 'utf8');

// Import stopGeneration from useChat
content = content.replace(
  /const \{ selectedAgent, isGenerating \} = useChat\(\);/g,
  `const { selectedAgent, isGenerating, stopGeneration } = useChat();`
);

// Update send/stop button logic
content = content.replace(
  /<button[\s\n]*type="button"[\s\n]*onClick=\{handleSubmit\}[\s\n]*disabled\{\(!input\.trim\(\) && !attachment\) \|\| isGenerating\}[\s\n]*className=\{`w-9 h-9 rounded-full flex items-center justify-center shadow-xs transition-all flex-shrink-0 \$\{[\s\n]*isGenerating[\s\n]*\? 'bg-slate-200 text-slate-500 cursor-not-allowed'[\s\n]*: !input\.trim\(\) && !attachment[\s\n]*\? 'bg-slate-100 text-slate-300 cursor-not-allowed'[\s\n]*: 'bg-blue-600 hover:bg-blue-700 text-white'[\s\n]*\}`\}[\s\n]*title=\{isGenerating \? 'Generating response\.\.\.' : 'Send message \(Enter\)'\}[\s\n]*aria-label="Send message"[\s\n]*>[\s\n]*\{isGenerating \? \([\s\n]*<Loader2 className="w-4 h-4 animate-spin text-slate-600" \/>[\s\n]*\) : \([\s\n]*<ArrowUp className="w-4 h-4 stroke-\[2\.5\]" \/>[\s\n]*\)\}[\s\n]*<\/button>/g,
  `<button
            type="button"
            onClick={isGenerating ? stopGeneration : handleSubmit}
            disabled={!isGenerating && !input.trim() && !attachment}
            className={\`w-9 h-9 rounded-full flex items-center justify-center shadow-xs transition-all flex-shrink-0 \${
              isGenerating
                ? 'bg-rose-500 hover:bg-rose-600 text-white'
                : !input.trim() && !attachment
                ? 'bg-slate-100 text-slate-300 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700 text-white'
            }\`}
            title={isGenerating ? 'Stop generating' : 'Send message (Enter)'}
            aria-label={isGenerating ? 'Stop generating' : 'Send message'}
          >
            {isGenerating ? (
              <span className="w-3.5 h-3.5 rounded-sm bg-white" />
            ) : (
              <ArrowUp className="w-4 h-4 stroke-[2.5]" />
            )}
          </button>`
);

fs.writeFileSync(inputBarPath, content, 'utf8');
console.log('ChatInputBar.jsx patched successfully!');
