const fs = require('fs');

const inputBarPath = 'FRONTEND/src/components/chat/ChatInputBar.jsx';
let content = fs.readFileSync(inputBarPath, 'utf8');

// Find the Send Button block
const buttonRegex = /\{\/\* Send Button \*\/\}\s*<button[\s\S]*?<\/button>/;

const newButton = `{/* Send Button */}
          <button
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
          </button>`;

content = content.replace(buttonRegex, newButton);

fs.writeFileSync(inputBarPath, content, 'utf8');
console.log('ChatInputBar.jsx patched properly!');
