
import os
import re

target_file = '/home/nethunter/Documents/TeleGhost/frontend/src/App.svelte'

with open(target_file, 'r') as f:
    content = f.read()

# Fix 1: Sidebar Folders HTML (Remove check for 'all', show name for all)
# Original:
# <div class="folder-icon">{@html folder.icon}</div>
# {#if folder.id === 'all'}
#    <div class="folder-name">Все чаты</div>
# {/if}
# New:
# <div class="folder-icon">{@html folder.icon}</div>
# <div class="folder-name">{folder.id === 'all' ? 'Все' : folder.name}</div>

# Regex approach might be tricky due to whitespace.
# We'll try string replacement if we can identify unique block.
folder_block_old = """          <div class="folder-icon">{@html folder.icon}</div>
          {#if folder.id === 'all'}
             <div class="folder-name">Все чаты</div>
          {/if}"""
folder_block_new = """          <div class="folder-icon">{@html folder.icon}</div>
          <div class="folder-name">{folder.id === 'all' ? 'Все' : folder.name}</div>"""

if folder_block_old in content:
    content = content.replace(folder_block_old, folder_block_new)
else:
    # Try regex if exact match fails
    pattern = r'<div class="folder-icon">{@html folder.icon}</div>\s+{#if folder\.id === \'all\'}\s+<div class="folder-name">Все чаты</div>\s+{/if}'
    replacement = '<div class="folder-icon">{@html folder.icon}</div>\n          <div class="folder-name">{folder.id === \'all\' ? \'Все\' : folder.name}</div>'
    content = re.sub(pattern, replacement, content)

# Fix 2: Limit Folder Name in Modal
# Find input for folder name
# <input type="text" class="input-field" placeholder="Название папки" bind:value={newFolderName} on:keydown={(e) => e.key === 'Enter' && createFolder()} autofocus />
input_old = 'bind:value={newFolderName} on:keydown={(e) => e.key === \'Enter\' && createFolder()} autofocus />'
input_new = 'bind:value={newFolderName} on:keydown={(e) => e.key === \'Enter\' && createFolder()} maxlength="12" autofocus />'
content = content.replace(input_old, input_new)

# Fix 3: Mobile Header Logic
# Old:
# <button class="btn-icon" on:click={toggleSettingsMobile}>
#     <div class="icon-svg">{@html Icons.Menu}</div>
# </button>
# New:
# <button class="btn-icon" on:click={() => $mobileView === 'list' ? toggleSettingsMobile() : goBack()}>
#     {#if $mobileView === 'list'}
#        <div class="icon-svg">{@html Icons.Menu}</div>
#     {:else}
#        <div class="icon-svg">{@html Icons.ArrowLeft}</div>
#     {/if}
# </button>

header_btn_old = """          <button class="btn-icon" on:click={toggleSettingsMobile}>
              <div class="icon-svg">{@html Icons.Menu}</div>
          </button>"""
header_btn_new = """          <button class="btn-icon" on:click={() => $mobileView === 'list' ? toggleSettingsMobile() : goBack()}>
              {#if $mobileView === 'list'}
                 <div class="icon-svg">{@html Icons.Menu}</div>
              {:else}
                 <div class="icon-svg">{@html Icons.ArrowLeft}</div>
              {/if}
          </button>"""

content = content.replace(header_btn_old, header_btn_new)

# Fix 3b: Remove duplicate settings header in Mobile Settings Container
# <div class="settings-header"> ... <h2>Настройки</h2> ... </div>
# Only in the block with class="mobile-settings-container"
# We can regex replace the whole block or just the header part inside it.
# The mobile-settings-container logic:
# {:else if $mobileView === 'settings'}
#      <div class="mobile-settings-container">
#          <div class="settings-header">
#              <button class="btn-icon" on:click={goBack}>
#                  <div class="icon-svg">{@html Icons.ArrowLeft}</div>
#              </button>
#              <h2>Настройки</h2>
#          </div>
# We want to remove this settings-header div entirely or empty it, as main mobile header handles it.
settings_header_block_old = """                   <div class="settings-header">
                       <button class="btn-icon" on:click={goBack}>
                           <div class="icon-svg">{@html Icons.ArrowLeft}</div>
                       </button>
                       <h2>Настройки</h2>
                   </div>"""
settings_header_block_new = "" # Remove it
content = content.replace(settings_header_block_old, settings_header_block_new)

# Fix 4: Double Context Menu
# on:contextmenu={(e) => showMessageMenu(e, msg)} -> on:contextmenu|preventDefault ...
msg_ctx_old = 'on:contextmenu={(e) => showMessageMenu(e, msg)}'
msg_ctx_new = 'on:contextmenu|preventDefault={(e) => showMessageMenu(e, msg)}'
content = content.replace(msg_ctx_old, msg_ctx_new)

# Fix 5: Mobile Viewport & CSS
# Add/Update CSS
# We'll append new CSS rules at the end of <style> block or replace existing if easy.
# Replacing existing .mobile-container to use 100dvh
css_mobile_container_old = """  .mobile-container {
      flex: 1;
      display: flex;
      flex-direction: column;
      height: 100vh;
      overflow: hidden;
      background: var(--bg-primary);
  }"""
css_mobile_container_new = """  .mobile-container {
      flex: 1;
      display: flex;
      flex-direction: column;
      height: 100dvh;
      overflow: hidden;
      background: var(--bg-primary);
  }"""
content = content.replace(css_mobile_container_old, css_mobile_container_new)

# Add .folder-item and .folder-name styles
# Also .mobile-input-area sticky
new_css = """
  /* === UI Fixes CSS === */
  .folder-item {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      width: 64px;
      height: 64px;
      margin-bottom: 8px;
      cursor: pointer;
      border-radius: 12px;
      transition: background 0.2s;
      gap: 2px;
  }
  .folder-item:hover, .folder-item.active {
      background: rgba(255, 255, 255, 0.1);
  }
  .folder-icon {
      font-size: 24px;
  }
  .folder-name {
      font-size: 10px;
      max-width: 100%;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      text-align: center;
      color: var(--text-secondary);
  }
  
  .mobile-input-area {
      position: sticky;
      bottom: 0;
      z-index: 50;
      background: var(--bg-secondary); /* Ensure visibility */
  }
</style>"""

content = content.replace('</style>', new_css)

with open(target_file, 'w') as f:
    f.write(content)

print("Updates applied successfully.")
