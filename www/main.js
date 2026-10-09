$(document).ready(function () {

    // ------------------------------------------------------------
    // Safe Markdown Parser (XSS-safe, code blocks, lists, typography)
    // ------------------------------------------------------------
    function escapeHtml(str) {
        if (!str) return "";
        return String(str)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function formatRelativeTime(isoString) {
        if (!isoString) return "";
        try {
            var date = new Date(isoString);
            if (isNaN(date.getTime())) return "";
            var now = new Date();
            var diffSec = Math.floor((now - date) / 1000);
            if (diffSec < 60) return "Just now";
            var diffMin = Math.floor(diffSec / 60);
            if (diffMin < 60) return diffMin + "m ago";
            var diffHour = Math.floor(diffMin / 60);
            if (diffHour < 24) return diffHour + "h ago";
            var diffDay = Math.floor(diffHour / 24);
            if (diffDay < 7) return diffDay + "d ago";
            return date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
        } catch (e) {
            return "";
        }
    }

    function renderMarkdownSafe(text) {
        if (!text) return "";
        var safe = String(text).trim();

        // 1. Extract and protect fenced code blocks
        var codeBlocks = [];
        safe = safe.replace(/```([a-zA-Z0-9_-]*)\r?\n([\s\S]*?)```/g, function (match, lang, code) {
            var id = codeBlocks.length;
            var escapedCode = escapeHtml(code.trim());
            var displayLang = escapeHtml(lang || "code");
            var blockHtml = `<div class="chat-code-block">
                <div class="chat-code-header">
                    <span class="chat-code-lang">${displayLang}</span>
                    <button type="button" class="chat-copy-code-btn">
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                        </svg>
                        <span>Copy</span>
                    </button>
                </div>
                <pre><code>${escapedCode}</code></pre>
            </div>`;
            codeBlocks.push(blockHtml);
            return `__CODE_BLOCK_${id}__`;
        });

        // 2. Escape remaining raw text to prevent XSS
        safe = escapeHtml(safe);

        // 3. Inline code
        safe = safe.replace(/`([^`]+)`/g, '<code class="chat-inline-code">$1</code>');

        // 4. Bold and italics
        safe = safe.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        safe = safe.replace(/\*([^*]+)\*/g, '<em>$1</em>');

        // 5. Headings
        safe = safe.replace(/^### (.*?)$/gm, '<h4>$1</h4>');
        safe = safe.replace(/^## (.*?)$/gm, '<h3>$1</h3>');
        safe = safe.replace(/^# (.*?)$/gm, '<h2>$1</h2>');

        // 6. Lists
        // Bullet lists
        safe = safe.replace(/(?:^[*-] .*(?:\r?\n|$))+/gm, function (match) {
            var items = match.trim().split(/\r?\n/).map(function (line) {
                return '<li>' + line.replace(/^[*-] /, '').trim() + '</li>';
            }).join('');
            return '<ul>' + items + '</ul>';
        });

        // Numbered lists
        safe = safe.replace(/(?:^\d+\. .*(?:\r?\n|$))+/gm, function (match) {
            var items = match.trim().split(/\r?\n/).map(function (line) {
                return '<li>' + line.replace(/^\d+\. /, '').trim() + '</li>';
            }).join('');
            return '<ol>' + items + '</ol>';
        });

        // 7. Paragraphs
        var paragraphs = safe.split(/\n{2,}/);
        safe = paragraphs.map(function (p) {
            p = p.trim();
            if (!p) return "";
            if (p.startsWith("<div class=\"chat-code-block\"") || p.startsWith("<ul>") || p.startsWith("<ol>") || p.startsWith("<h")) {
                return p;
            }
            return '<p>' + p.replace(/\n/g, '<br>') + '</p>';
        }).join('');

        // 8. Re-insert code blocks
        codeBlocks.forEach(function (html, i) {
            safe = safe.replace(new RegExp('__CODE_BLOCK_' + i + '__', 'g'), html);
        });

        return safe;
    }

    // ------------------------------------------------------------
    // Persistent Conversation State & View Management
    // ------------------------------------------------------------
    var activeConversationId = null;
    var lastUserMessageText = "";
    var lastAssistantMessageText = "";

    function scrollToBottom(force) {
        var container = document.getElementById("conversationView");
        if (!container) return;
        var isNearBottom = (container.scrollHeight - container.scrollTop - container.clientHeight) < 140;
        if (force || isNearBottom) {
            container.scrollTop = container.scrollHeight;
        }
    }

    function activateConversationMode() {
        var $main = $("#oval");
        if (!$main.hasClass("conversation-active")) {
            $main.addClass("conversation-active");
            $("#heroSection").hide();
            $("#toolsSection").hide();
            $("#conversationView").css("display", "flex").show();
            $("#newChatBtn").css("display", "inline-flex").show();
        }
    }

    function startNewChat() {
        activeConversationId = null;
        $("#chatMessages").empty();
        $("#oval").removeClass("conversation-active");
        $("#conversationView").hide();
        $("#heroSection").show();
        $("#toolsSection").show();
        $("#newChatBtn").hide();
        $("#siriwave").attr("hidden", true);
        removeTypingIndicator();
        lastUserMessageText = "";
        lastAssistantMessageText = "";
        $(".recent-chat-item").removeClass("active");
        $("#chatbot").val("").focus();
    }

    function appendUserMessage(text) {
        if (!text || String(text).trim() === "") return;
        var cleanText = String(text).trim();

        // Deduplication check
        if (cleanText === lastUserMessageText && $("#chatMessages .chat-user-row").length > 0) {
            return;
        }
        lastUserMessageText = cleanText;

        activateConversationMode();

        var html = `<div class="chat-user-row">
            <div class="chat-user-bubble">${escapeHtml(cleanText)}</div>
        </div>`;

        $("#chatMessages").append(html);
        scrollToBottom(true);
    }

    function showTypingIndicator() {
        if ($("#chatTypingIndicator").length > 0) return;
        activateConversationMode();

        var html = `<div class="chat-typing-row" id="chatTypingIndicator">
            <div class="chat-assistant-avatar" aria-hidden="true">
                <svg width="17" height="17" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2L14.2 9.8L22 12L14.2 14.2L12 22L9.8 14.2L2 12L9.8 9.8L12 2Z"/>
                </svg>
            </div>
            <div class="typing-bubble">
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
            </div>
        </div>`;

        $("#chatMessages").append(html);
        scrollToBottom(false);
    }

    function removeTypingIndicator() {
        $("#chatTypingIndicator").remove();
    }

    function appendAssistantMessage(text) {
        if (!text || String(text).trim() === "") return;
        var cleanText = String(text).trim();

        removeTypingIndicator();

        // Deduplication check
        if (cleanText === lastAssistantMessageText && $("#chatMessages .chat-assistant-row").length > 0) {
            return;
        }
        lastAssistantMessageText = cleanText;

        activateConversationMode();

        var formattedContent = renderMarkdownSafe(cleanText);
        var html = `<div class="chat-assistant-row">
            <div class="chat-assistant-avatar" aria-hidden="true">
                <svg width="17" height="17" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2L14.2 9.8L22 12L14.2 14.2L12 22L9.8 14.2L2 12L9.8 9.8L12 2Z"/>
                </svg>
            </div>
            <div class="chat-assistant-body">
                ${formattedContent}
            </div>
        </div>`;

        $("#chatMessages").append(html);
        scrollToBottom(false);
    }

    // ------------------------------------------------------------
    // Recent Chats History Operations (SQLite Backed)
    // ------------------------------------------------------------

    function loadRecentConversations() {
        if (typeof eel === "undefined" || !eel.getRecentConversations) return;
        try {
            eel.getRecentConversations()(function (res) {
                if (!res || res.status !== "success" || !Array.isArray(res.conversations)) {
                    return;
                }
                var convs = res.conversations;
                var $list = $("#recentChatsList");
                $list.empty();

                if (convs.length === 0) {
                    $("#recentChatsEmpty").show();
                    return;
                }

                $("#recentChatsEmpty").hide();

                convs.forEach(function (conv) {
                    var isActive = (conv.id === activeConversationId);
                    var dateStr = formatRelativeTime(conv.updated_at);
                    var itemHtml = `
                    <div class="recent-chat-item ${isActive ? 'active' : ''}" data-id="${escapeHtml(conv.id)}">
                        <div class="recent-chat-main">
                            <span class="recent-chat-icon"><i class="bi bi-chat-text"></i></span>
                            <div class="recent-chat-text-group">
                                <span class="recent-chat-title" title="${escapeHtml(conv.title)}">${escapeHtml(conv.title)}</span>
                                <span class="recent-chat-date">${escapeHtml(dateStr)}</span>
                            </div>
                        </div>
                        <div class="recent-chat-actions">
                            <button type="button" class="recent-chat-action-btn btn-rename" title="Rename conversation" data-id="${escapeHtml(conv.id)}" data-title="${escapeHtml(conv.title)}">
                                <i class="bi bi-pencil"></i>
                            </button>
                            <button type="button" class="recent-chat-action-btn btn-delete" title="Delete conversation" data-id="${escapeHtml(conv.id)}">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                    </div>`;
                    $list.append(itemHtml);
                });
            });
        } catch (err) {
            console.warn("Failed to load recent conversations:", err);
        }
    }

    function selectConversation(convId) {
        if (!convId || typeof eel === "undefined" || !eel.getConversationMessages) return;

        eel.getConversationMessages(convId)(function (res) {
            if (!res || res.status !== "success" || !Array.isArray(res.messages)) {
                showToast("Could not load conversation");
                return;
            }

            activeConversationId = convId;
            lastUserMessageText = "";
            lastAssistantMessageText = "";

            $("#chatMessages").empty();
            activateConversationMode();

            // Render all historical messages
            res.messages.forEach(function (msg) {
                if (msg.role === "user") {
                    var userHtml = `<div class="chat-user-row">
                        <div class="chat-user-bubble">${escapeHtml(msg.content)}</div>
                    </div>`;
                    $("#chatMessages").append(userHtml);
                } else if (msg.role === "assistant") {
                    var formatted = renderMarkdownSafe(msg.content);
                    var assistantHtml = `<div class="chat-assistant-row">
                        <div class="chat-assistant-avatar" aria-hidden="true">
                            <svg width="17" height="17" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M12 2L14.2 9.8L22 12L14.2 14.2L12 22L9.8 14.2L2 12L9.8 9.8L12 2Z"/>
                            </svg>
                        </div>
                        <div class="chat-assistant-body">
                            ${formatted}
                        </div>
                    </div>`;
                    $("#chatMessages").append(assistantHtml);
                }
            });

            scrollToBottom(true);

            // Highlight active item in recent chats list
            $(".recent-chat-item").removeClass("active");
            $(`.recent-chat-item[data-id="${convId}"]`).addClass("active");

            // Close offcanvas drawer cleanly
            var drawerEl = document.getElementById("offcanvasScrolling");
            if (drawerEl && typeof bootstrap !== "undefined") {
                var bsOffcanvas = bootstrap.Offcanvas.getInstance(drawerEl);
                if (bsOffcanvas) {
                    bsOffcanvas.hide();
                }
            }

            $("#chatbot").focus();
        });
    }

    function deleteConversation(convId) {
        if (!convId || typeof eel === "undefined" || !eel.deleteConversation) return;

        var confirmed = window.confirm("Are you sure you want to delete this conversation?");
        if (!confirmed) return;

        eel.deleteConversation(convId)(function (res) {
            if (res && res.status === "success") {
                showToast("Conversation deleted");
                if (activeConversationId === convId) {
                    startNewChat();
                }
                loadRecentConversations();
            } else {
                showToast("Failed to delete conversation");
            }
        });
    }

    function renameConversation(convId, currentTitle) {
        if (!convId || typeof eel === "undefined" || !eel.renameConversation) return;

        var newTitle = window.prompt("Enter new conversation title:", currentTitle || "");
        if (newTitle === null) return;
        var cleanTitle = newTitle.trim();
        if (!cleanTitle) {
            showToast("Title cannot be empty");
            return;
        }

        eel.renameConversation(convId, cleanTitle)(function (res) {
            if (res && res.status === "success") {
                showToast("Conversation renamed");
                loadRecentConversations();
            } else {
                showToast("Failed to rename conversation");
            }
        });
    }

    // Export interface for controller.js and global coordination
    window.JarvisChat = {
        activateConversationMode: activateConversationMode,
        appendUserMessage: appendUserMessage,
        appendAssistantMessage: appendAssistantMessage,
        showTypingIndicator: showTypingIndicator,
        removeTypingIndicator: removeTypingIndicator,
        startNewChat: startNewChat,
        scrollToBottom: scrollToBottom,
        loadRecentConversations: loadRecentConversations,
        selectConversation: selectConversation,
        getActiveConversationId: function () { return activeConversationId; },
        setActiveConversationId: function (id) { activeConversationId = id; }
    };
    window.selectConversation = selectConversation;
    window.startNewChat = startNewChat;
    window.loadRecentConversations = loadRecentConversations;

    // ------------------------------------------------------------
    // Code Copy Button Handler
    // ------------------------------------------------------------
    $(document).on("click", ".chat-copy-code-btn", function () {
        var $btn = $(this);
        var code = $btn.closest(".chat-code-block").find("pre code").text();
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(code).then(function () {
                $btn.find("span").text("Copied!");
                setTimeout(function () {
                    $btn.find("span").text("Copy");
                }, 2000);
            }).catch(function () {
                copyFallback(code, $btn);
            });
        } else {
            copyFallback(code, $btn);
        }
    });

    function copyFallback(code, $btn) {
        var textarea = document.createElement("textarea");
        textarea.value = code;
        textarea.style.position = "fixed";
        textarea.style.opacity = "0";
        document.body.appendChild(textarea);
        textarea.select();
        try {
            document.execCommand("copy");
            $btn.find("span").text("Copied!");
            setTimeout(function () {
                $btn.find("span").text("Copy");
            }, 2000);
        } catch (e) {
            // Ignore
        }
        document.body.removeChild(textarea);
    }

    // ------------------------------------------------------------
    // Compact SiriWave Dock Initialization
    // ------------------------------------------------------------
    var siriWave = null;
    var siriContainer = document.getElementById("siri-container");
    if (siriContainer && typeof SiriWave !== "undefined") {
        try {
            siriWave = new SiriWave({
                container: siriContainer,
                width: 240,
                height: 38,
                style: "ios9",
                amplitude: 1,
                speed: 0.30,
                autostart: true
            });
        } catch (err) {
            console.warn("SiriWave initialization:", err);
        }
    }

    // Toast notification helper
    function showToast(message, duration = 3000) {
        var $toast = $("#jarvisToast");
        if ($toast.length) {
            $toast.text(message).addClass("show");
            setTimeout(function () {
                $toast.removeClass("show");
            }, duration);
        }
    }

    // ------------------------------------------------------------
    // Voice Listening Operations
    // ------------------------------------------------------------
    function startVoiceListening() {
        activateConversationMode();
        $("#siriwave").removeAttr("hidden");
        $(".siri-message").text("Listening...");

        if (typeof eel !== "undefined" && eel.playAssistantSound) {
            eel.playAssistantSound();
        }
        if (typeof eel !== "undefined" && eel.allCommands) {
            eel.allCommands(1, activeConversationId)();
        }
    }

    // Cancel listening button in compact SiriWave dock
    $("#siriCancelBtn").click(function () {
        $("#siriwave").attr("hidden", true);
        removeTypingIndicator();
        $(".siri-message").text("Idle");
    });

    // Mic Button click handler (Sparkle circular button)
    $("#MicBtn").click(function () {
        startVoiceListening();
    });

    // Keyboard shortcut Win+J or Cmd+J
    function doc_keyUp(e) {
        if (e.key === 'j' && (e.metaKey || e.ctrlKey)) {
            startVoiceListening();
        }
    }
    document.addEventListener('keyup', doc_keyUp, false);

    // ------------------------------------------------------------
    // Text Assistant Command Dispatcher
    // ------------------------------------------------------------
    function PlayAssistant(message) {
        if (message && String(message).trim() !== "") {
            var query = String(message).trim();
            activateConversationMode();
            appendUserMessage(query);
            showTypingIndicator();
            $(".siri-message").text("Thinking...");

            if (typeof eel !== "undefined" && eel.allCommands) {
                eel.allCommands(query, activeConversationId);
            }
            $("#chatbot").val("");
        }
    }

    // Send Button click handler (White circular up-arrow button)
    $("#SendBtn").click(function () {
        var message = $("#chatbot").val();
        if (message && String(message).trim() !== "") {
            PlayAssistant(message);
        } else {
            startVoiceListening();
        }
    });

    // Enter press on chatbot input
    $("#chatbot").keypress(function (e) {
        if (e.which === 13) {
            var message = $("#chatbot").val();
            if (message && String(message).trim() !== "") {
                PlayAssistant(message);
            }
        }
    });

    // New Chat Header and Drawer Buttons
    $("#newChatBtn").click(function () {
        startNewChat();
    });

    $("#drawerNewChatBtn").click(function () {
        startNewChat();
        var drawerEl = document.getElementById("offcanvasScrolling");
        if (drawerEl && typeof bootstrap !== "undefined") {
            var bsOffcanvas = bootstrap.Offcanvas.getInstance(drawerEl);
            if (bsOffcanvas) {
                bsOffcanvas.hide();
            }
        }
    });

    // Brand click returns to home screen
    $(".brand-container").click(function () {
        startNewChat();
    });

    // Recent chats list item click delegation
    $(document).on("click", ".recent-chat-item", function (e) {
        if ($(e.target).closest(".recent-chat-actions").length > 0) {
            return;
        }
        var convId = $(this).attr("data-id");
        if (convId) {
            selectConversation(convId);
        }
    });

    // Rename button click delegation
    $(document).on("click", ".btn-rename", function (e) {
        e.stopPropagation();
        var convId = $(this).attr("data-id");
        var title = $(this).attr("data-title");
        renameConversation(convId, title);
    });

    // Delete button click delegation
    $(document).on("click", ".btn-delete", function (e) {
        e.stopPropagation();
        var convId = $(this).attr("data-id");
        deleteConversation(convId);
    });

    // Search pill button
    $("#SearchPillBtn").click(function () {
        var current = $("#chatbot").val().trim();
        if (current.length > 0) {
            if (!current.toLowerCase().startsWith("search")) {
                PlayAssistant("search " + current);
            } else {
                PlayAssistant(current);
            }
        } else {
            $("#chatbot").val("search ").focus();
            showToast("Enter a topic to search and press Enter");
        }
    });

    // Create Image pill button
    $("#CreateImagePillBtn").click(function () {
        showToast("Image generation model integration is currently in development");
    });

    // Ambient lightbulb button
    $("#lightbulbBtn").click(function () {
        $("body").toggleClass("ambient-boost");
        showToast("Ambient lighting adjusted");
    });

    // Feature card click shortcuts
    $("#cardLaunchAssistant").click(function () {
        $("#chatbot").val("help me configure an assistant").focus();
    });

    $("#cardFineTune").click(function () {
        $("#chatbot").val("how can I fine-tune a model").focus();
    });

    // ------------------------------------------------------------
    // Profile avatar click handler — Open Flask Admin Dashboard
    // ------------------------------------------------------------
    var isOpeningDashboard = false;
    $("#profileAvatar").click(function (e) {
        if (e) {
            e.preventDefault();
            e.stopPropagation();
        }

        if (isOpeningDashboard) {
            return;
        }
        isOpeningDashboard = true;

        var unlockTimer = setTimeout(function () {
            isOpeningDashboard = false;
        }, 3000);

        if (typeof eel !== "undefined" && eel.openAdminDashboard) {
            try {
                eel.openAdminDashboard()(function (res) {
                    clearTimeout(unlockTimer);
                    isOpeningDashboard = false;
                    if (res && res.status === "error") {
                        showToast(res.message, 4500);
                    } else if (res && res.status === "success") {
                        showToast("Opening Admin Dashboard...", 3000);
                    }
                });
            } catch (err) {
                clearTimeout(unlockTimer);
                isOpeningDashboard = false;
                showToast("Failed to communicate with assistant engine", 3000);
            }
        } else {
            clearTimeout(unlockTimer);
            setTimeout(function () {
                isOpeningDashboard = false;
            }, 800);
            try {
                window.open("http://127.0.0.1:5005/admin", "_blank");
            } catch (err) {
                // Ignore popup blocker
            }
            showToast("Opening Admin Dashboard...", 3000);
        }
    });

    // Load recent chats from SQLite on application initialization
    loadRecentConversations();

});