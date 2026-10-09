$(document).ready(function () {

    // Helper: update offcanvas drawer for backwards compatibility
    function updateOffcanvasSender(message) {
        var chatBox = document.getElementById("chat-canvas-body");
        if (chatBox && message && String(message).trim() !== "") {
            chatBox.innerHTML += `<div class="row justify-content-end mb-3">
                <div class="width-size">
                    <div class="sender_message">${message}</div>
                </div>
            </div>`;
            chatBox.scrollTop = chatBox.scrollHeight;
        }
    }

    function updateOffcanvasReceiver(message) {
        var chatBox = document.getElementById("chat-canvas-body");
        if (chatBox && message && String(message).trim() !== "") {
            chatBox.innerHTML += `<div class="row justify-content-start mb-3">
                <div class="width-size">
                    <div class="receiver_message">${message}</div>
                </div>
            </div>`;
            chatBox.scrollTop = chatBox.scrollHeight;
        }
    }

    // Display Speak / Voice status message from Python backend
    eel.expose(DisplayMessage);
    function DisplayMessage(message, convId) {
        if (!message) return;
        var str = String(message).trim();
        var lower = str.toLowerCase();

        // 1. Voice recognition lifecycle updates
        if (lower === "listening..." || lower === "recognizing...") {
            $(".siri-message").text(str);
            $("#siriwave").removeAttr("hidden");
            if (lower === "recognizing..." && window.JarvisChat) {
                window.JarvisChat.showTypingIndicator();
            }
            return;
        }

        // 2. Assistant response from speak_fn / speech synthesis
        $(".siri-message").text("Speaking...");

        if (window.JarvisChat) {
            var activeId = window.JarvisChat.getActiveConversationId();
            if (!activeId && convId) {
                window.JarvisChat.setActiveConversationId(convId);
                activeId = convId;
            }

            // Safe session routing: only append to active view if conversation matches
            if (convId && activeId && convId !== activeId) {
                window.JarvisChat.loadRecentConversations();
                return;
            }

            window.JarvisChat.appendAssistantMessage(str);
            window.JarvisChat.loadRecentConversations();
        }

        // Update legacy offcanvas drawer container
        updateOffcanvasReceiver(str);
    }

    // Restore Main Dashboard Hood when speech/command completes
    eel.expose(ShowHood);
    function ShowHood(convId) {
        $("#oval").removeAttr("hidden");
        $("#siriwave").attr("hidden", true);
        if (window.JarvisChat) {
            window.JarvisChat.removeTypingIndicator();
            window.JarvisChat.loadRecentConversations();
        }
        $(".siri-message").text("Idle");
    }

    // Append user's query to chat
    eel.expose(senderText);
    function senderText(message, convId) {
        if (!message || String(message).trim() === "") return;
        var clean = String(message).trim();

        if (window.JarvisChat) {
            var activeId = window.JarvisChat.getActiveConversationId();
            if (!activeId && convId) {
                window.JarvisChat.setActiveConversationId(convId);
                activeId = convId;
            }

            // Safe session routing: only append to active view if conversation matches
            if (!convId || !activeId || convId === activeId) {
                window.JarvisChat.appendUserMessage(clean);
                window.JarvisChat.showTypingIndicator();
            }
            window.JarvisChat.loadRecentConversations();
        }

        // Update legacy offcanvas drawer container
        updateOffcanvasSender(clean);
    }

    // Append assistant's response to chat
    eel.expose(receiverText);
    function receiverText(message, convId) {
        if (!message || String(message).trim() === "") return;
        var clean = String(message).trim();

        if (window.JarvisChat) {
            var activeId = window.JarvisChat.getActiveConversationId();
            if (!convId || !activeId || convId === activeId) {
                window.JarvisChat.appendAssistantMessage(clean);
            }
            window.JarvisChat.loadRecentConversations();
        }

        // Update legacy offcanvas drawer container
        updateOffcanvasReceiver(clean);
    }

});