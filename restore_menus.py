
import os

file_path = '/home/nethunter/Documents/TeleGhost/frontend/src/App.svelte'

contact_menu = """
<!-- Context Menu for Contacts -->
{#if contextMenu.show}
<div class="context-menu" style="top: {contextMenu.y}px; left: {contextMenu.x}px" on:click|stopPropagation>
    <!-- Folder actions -->
    {#if folders.length > 0}
        <div class="context-header" style="padding: 8px 12px; font-size: 12px; opacity: 0.5;">ПАПКИ</div>
        {#each folders as folder (folder.id)}
            {#if folder.chatIds && folder.chatIds.includes(contextMenu.contact.id)}
                <div class="context-item" on:click={() => { removeChatFromFolder(folder.id, contextMenu.contact.id); contextMenu.show = false; }}>
                    <span class="icon-svg-sm" style="display:inline-block; vertical-align:middle; margin-right:4px;">{@html Icons.X}</span> Из "{folder.name}"
                </div>
            {:else}
                <div class="context-item" on:click={() => { addChatToFolder(folder.id, contextMenu.contact.id); contextMenu.show = false; }}>
                    <span class="icon-svg-sm" style="display:inline-block; vertical-align:middle; margin-right:4px;">{@html Icons.Plus}</span> В "{folder.name}"
                </div>
            {/if}
        {/each}
        <div class="divider" style="height: 1px; background: var(--border); margin: 4px 0;"></div>
    {/if}

    <div class="context-item" on:click={copyAddressFromMenu}>Скопировать адрес</div>
    <div class="context-item" style="color: #ff6b6b;" on:click={deleteContactFromMenu}>Удалить контакт</div>
</div>
{/if}
"""

message_menu = """
<!-- Context Menu for Messages/Files -->
{#if messageContextMenu.show}
<div class="context-menu" style="top: {messageContextMenu.y}px; left: {messageContextMenu.x}px" on:click|stopPropagation>
    {#if messageContextMenu.imagePath}
        <div class="context-item" on:click={() => copyImageToClipboard(messageContextMenu.imagePath)}>Скопировать картинку</div>
        <div class="context-item" on:click={() => showInFolder(messageContextMenu.imagePath)}>Показать в папке</div>
    {:else if messageContextMenu.filePath}
        <div class="context-item" on:click={() => openFile(messageContextMenu.filePath)}>Открыть файл</div>
        <div class="context-item" on:click={() => copyPathToClipboard(messageContextMenu.filePath)}>Скопировать путь</div>
        <div class="context-item" on:click={() => showInFolder(messageContextMenu.filePath)}>Показать в папке</div>
    {:else}
        {#if messageContextMenu.message && !messageContextMenu.message.isOutgoing}
             <!-- Incoming message options -->
             <div class="context-item" on:click={() => { navigator.clipboard.writeText(messageContextMenu.message.content); messageContextMenu.show=false; }}>Скопировать текст</div>
        {:else}
             <!-- Outgoing message options -->
             <div class="context-item" on:click={() => startEditMessage(messageContextMenu.message)}>Редактировать</div>
             <div class="context-item" on:click={() => { navigator.clipboard.writeText(messageContextMenu.message.content); messageContextMenu.show=false; }}>Скопировать текст</div>
        {/if}
    {/if}
    
    {#if messageContextMenu.message}
        <div class="context-item" style="color: #ff6b6b;" on:click={() => deleteMsg(messageContextMenu.message)}>Удалить у себя</div>
        <div class="context-item" style="color: #ff6b6b;" on:click={() => deleteMsg(messageContextMenu.message, true)}>Удалить у всех</div>
    {/if}
</div>
{/if}
"""

with open(file_path, 'a') as f:
    f.write(contact_menu)
    f.write(message_menu)

print("Restored context menus.")
