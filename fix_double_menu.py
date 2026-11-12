
import re
import os

file_path = '/home/nethunter/Documents/TeleGhost/frontend/src/App.svelte'

if not os.path.exists(file_path):
    print("File not found!")
    exit(1)

with open(file_path, 'r') as f:
    content = f.read()

print(f"Original length: {len(content)}")

# 1. REMOVE OLD CONTEXT MENUS (approx lines 1184-1232)
# We look for the block starting with "<!-- Context Menu for Contacts -->" AND containing "ПАПКИ" (Folders).
# Validating we are targeting the OLD one.

old_menu_start = "<!-- Context Menu for Contacts -->"
old_menu_end = "<!-- Contact Profile Modal -->"

if old_menu_start in content:
    parts = content.split(old_menu_start)
    # We expect parts to be at least 3 if there are 2 menus (one old, one new).
    # But wait, the NEW menu at the bottom ALSO starts with "<!-- Context Menu for Contacts -->".
    # And we just want to remove the FIRST one (which is the old one).
    
    if len(parts) >= 2:
        # Check if parts[1] contains "ПАПКИ" (unique to old menu)
        # parts[1] starts right after the first <!-- Context Menu for Contacts -->
        if "ПАПКИ" in parts[1]:
            print("Found old context menu block (first occurrence). Removing it...")
            
            # Find the end of this block
            # The block ends before <!-- Contact Profile Modal -->
            if old_menu_end in parts[1]:
                menu_content, rest_of_file = parts[1].split(old_menu_end, 1)
                
                # Reconstruct: 
                # parts[0] + [removed block replaced by nothing] + old_menu_end + rest_of_file
                # Wait, do we want to keep old_menu_end comment? Yes.
                
                # Also, we need to be careful about the Message menu.
                # The old Message menu is INSIDE this block (between Contacts and Profile Modal).
                # See file content: Contacts Menu -> Messages Menu -> Profile Modal.
                # So by removing from "Context Menu for Contacts" to "Profile Modal", 
                # we remove BOTH old menus (Contacts + Messages).
                # This is EXACTLY what we want!
                
                new_content = parts[0] + old_menu_end + rest_of_file
                content = new_content
                print("Removed duplicates successfully.")
            else:
                print("Error: Could not find end marker 'Contact Profile Modal' after old menu.")
        else:
             print("First occurrence does not look like the old menu (missing 'ПАПКИ').")
    else:
        print("Only one or zero context menus found. Check manual verification.")
else:
    print("Start marker not found.")


# 2. UPDATE NEW CONTEXT MENU
# Find the remaining "Context Menu for Contacts" block and inject folder logic.
# It should be the only one now.

# Regex to find the opening of the block
# It looks like:
# <!-- Context Menu for Contacts -->
# {#if contextMenu.show}
# <div class="context-menu" ...>

regex_header = r'(<!-- Context Menu for Contacts -->\s*\{#if contextMenu\.show\}\s*<div class="context-menu"[^>]*>)'

match = re.search(regex_header, content)
if match:
    print("Found new context menu block. Updating...")
    header = match.group(1)
    
    # Add stopPropagation if missing
    if "stopPropagation" not in header:
        header = header.replace('class="context-menu"', 'class="context-menu" on:click|stopPropagation')
    
    folder_logic = """
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
    """
    
    # Replace the header with header + folder_logic
    # But wait, re.sub replaces the MATCH.
    # We want to insert AFTER the opening div tag.
    # The regex matched up to the closing `>` of `<div ...>`.
    # So replacing match with match + usage is correct.
    
    content = content.replace(match.group(1), header + folder_logic)
    
else:
    print("Could not find new context menu block to update.")

# 3. FIX MESSAGE MENU STOP_PROPAGATION
# Ensure the message menu also has stopPropagation on the container.
# <!-- Context Menu for Messages/Files -->
# {#if messageContextMenu.show}
# <div class="context-menu" ...>

regex_msg_header = r'(<!-- Context Menu for Messages/Files -->\s*\{#if messageContextMenu\.show\}\s*<div class="context-menu"[^>]*>)'
match_msg = re.search(regex_msg_header, content)
if match_msg:
    msg_header = match_msg.group(1)
    if "stopPropagation" not in msg_header:
         print("Adding stopPropagation to Message Menu...")
         new_msg_header = msg_header.replace('class="context-menu"', 'class="context-menu" on:click|stopPropagation')
         content = content.replace(msg_header, new_msg_header)

with open(file_path, 'w') as f:
    f.write(content)

print("Done.")
