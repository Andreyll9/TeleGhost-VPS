
import os

target_file = '/home/nethunter/Documents/TeleGhost/frontend/src/App.svelte'

with open(target_file, 'r') as f:
    lines = f.readlines()

new_lines = []
skip_mode = False
replaced_settings = False

settings_replacement = """                        <div class="settings-details animate-slide-in-right">
                            <button class="btn-text" on:click={backToSettingsMenu} style="padding: 10px; display:flex; align-items:center; gap:6px;">
                                 <div class="icon-svg-sm">{@html Icons.ArrowLeft}</div> Назад
                            </button>
                            
                            <div class="settings-content-area" style="padding: 20px;">
                                {#if activeSettingsTab === 'profile'}
                                   <!-- Profile Content -->
                                   <div class="settings-section">
                                     <!-- Avatar -->
                                     <div class="profile-avatar-large" style="width: 120px; height: 120px; position: relative; margin: 0 auto;">
                                         {#if profileAvatar}
                                           <img src={profileAvatar} alt="Avatar" style="width: 100%; height: 100%; object-fit: cover; border-radius: 50%; box-shadow: 0 5px 15px rgba(0,0,0,0.3);" />
                                         {:else}
                                           <div style="width: 100%; height: 100%; background: linear-gradient(135deg, #6c5ce7, #a29bfe); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 48px; color: white; box-shadow: 0 5px 15px rgba(0,0,0,0.3);">
                                             {getInitials(profileNickname)}
                                           </div>
                                         {/if}
                                         <button class="avatar-edit-btn animate-pop" style="position: absolute; bottom: 0; right: 0; background: var(--accent); border: 4px solid var(--bg-primary); border-radius: 50%; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; cursor: pointer; color: white; box-shadow: 0 2px 5px rgba(0,0,0,0.2);" on:click={() => avatarFileInput.click()}><div class="icon-svg-sm">{@html Icons.Camera}</div></button>
                                         <input type="file" bind:this={avatarFileInput} on:change={handleAvatarChange} accept="image/*" style="display: none;" />
                                     </div>
                                     
                                     <div class="profile-fields" style="margin-top: 32px; max-width: 500px; margin-left: auto; margin-right: auto;">
                                       <label class="form-label" style="color: var(--text-primary);">Никнейм
                                         <input type="text" bind:value={profileNickname} class="input-field" placeholder="Ваш никнейм" />
                                       </label>
                                       <label class="form-label" style="margin-top: 24px; color: var(--text-primary);">О себе
                                         <textarea bind:value={profileBio} class="input-field" rows="3" placeholder="Расскажите о себе..."></textarea>
                                       </label>
                                       <button class="btn-primary" style="margin-top: 32px; width: 100%;" on:click={saveProfile}>💾 Сохранить изменения</button>
                                     </div>
                                   </div>

                                {:else if activeSettingsTab === 'chats'}
                                   <!-- Chats Content -->
                                   <div class="settings-section">
                                      <p class="hint" style="color: var(--text-secondary);">Здесь будут настройки темы, шрифта и фона чата.</p>
                                      <div class="mock-setting" style="margin-top: 20px; opacity: 0.5;">
                                         <label style="color: var(--text-primary);">Размер шрифта</label>
                                         <input type="range" min="12" max="20" value="14" disabled />
                                      </div>
                                   </div>

                                {:else if activeSettingsTab === 'privacy'}
                                   <!-- Privacy Content -->
                                   <div class="settings-section">
                                      <div class="info-box" style="background: rgba(255, 100, 100, 0.1); padding: 24px; border-radius: 12px; border: 1px solid rgba(255, 100, 100, 0.3);">
                                         <h4 style="color: #ff6b6b; margin: 0 0 12px; font-size: 18px;">🔐 Секретный ключ (Seed phrase)</h4>
                                         <p style="font-size: 14px; color: var(--text-secondary); margin-bottom: 20px;">Ваш ключ хранится только на этом устройстве. Если вы потеряете его, доступ к аккаунту будет утерян навсегда.</p>
                                         <button class="btn-secondary" style="width: 100%;" on:click={() => showToast('Функция показа ключа в разработке', 'warning')}>Показать ключ</button>
                                      </div>
                                   </div>

                                {:else if activeSettingsTab === 'network'}
                                   <!-- Network Content -->
                                   <div class="settings-section">
                                      <label class="form-label" style="color: var(--text-primary);">Ваш I2P адрес (Destination)</label>
                                      <div class="destination-box">
                                        <code class="destination-code">{myDestination ? myDestination.slice(0, 50) + '...' : 'Загрузка...'}</code>
                                        <button class="btn-icon-small" on:click={copyDestination}>📋</button>
                                      </div>
                                      <div class="info-item" style="margin-top: 20px;">
                                       <span class="info-label" style="color: var(--text-primary);">Статус сети:</span>
                                       <span class="info-value" style="color: {getStatusColor(networkStatus)}">{getStatusText(networkStatus)}</span>
                                      </div>

                                      <h4 style="margin-top: 32px; color: var(--text-primary); border-top: 1px solid var(--border); padding-top: 24px; font-size: 18px;">Настройки роутера</h4>
                                      <div class="settings-section">
                                         <!-- Tunnel Length -->
                                         <div class="setting-item" style="margin-bottom: 24px;">
                                             <label class="form-label" style="color: var(--text-primary); display: block; margin-bottom: 12px;">Режим анонимности (длина туннелей)</label>
                                             <select bind:value={routerSettings.tunnelLength} class="input-field settings-select">
                                                 <option value={1}>Fast (1 хоп) - Максимальная скорость, низкая анонимность</option>
                                                 <option value={2}>Normal (2 хопа) - Баланс (Рекомендуется)</option>
                                                 <option value={4}>Invisible (4 хопа) - Высокая анонимность, медленно</option>
                                             </select>
                                         </div>

                                         <!-- Logging -->
                                         <div class="setting-item" style="margin-bottom: 24px; display: flex; align-items: center; justify-content: space-between; background: var(--bg-secondary); padding: 16px; border-radius: 12px;">
                                             <div>
                                                 <span style="color: var(--text-primary); font-weight: 500;">Логирование в файл</span>
                                                 <p style="margin: 4px 0 0; font-size: 13px; color: var(--text-secondary);">Записывать логи роутера в i2pd.log</p>
                                             </div>
                                             <input type="checkbox" bind:checked={routerSettings.logToFile} style="transform: scale(1.5); cursor: pointer;" />
                                         </div>

                                         <button class="btn-primary" on:click={saveRouterSettings} style="width: 100%;">💾 Сохранить и применить</button>
                                         <p style="margin-top: 12px; font-size: 13px; color: var(--text-secondary); text-align: center;">Для вступления в силу изменений потребуется перезапуск приложения.</p>
                                      </div>
                                   </div>

                                {:else if activeSettingsTab === 'about'}
                                   <!-- About Content -->
                                   <h3 style="margin-bottom: 24px; font-size: 24px; color: var(--text-primary);">О программе</h3>
                                   <div class="info-grid">
                                     <div class="info-item"><span class="info-label">Версия</span><span class="info-value">1.1.0-beta</span></div>
                                     <div class="info-item"><span class="info-label">Разработчик</span><span class="info-value">TeleGhost Team</span></div>
                                     <div class="info-item"><span class="info-label">Лицензия</span><span class="info-value">MIT / Open Source</span></div>
                                   </div>
                                {/if}
                            </div>
                        </div>
"""

for i, line in enumerate(lines):
    # Fix message interactions
    if '<img use:startLoadingImage' in line and 'on:click={(e) => previewImage' in line:
        line = line.replace('on:click={', 'on:click|stopPropagation={')
    if '<div class="file-attachment-card"' in line and 'on:click={' in line:
        line = line.replace('on:click={', 'on:click|stopPropagation={')
    if '<div class="message-edit-actions">' in line:
        line = line.replace('on:click={', 'on:click|stopPropagation={')
    if '<button class="btn-small btn-success"' in line and 'acceptTransfer' in line:
        line = line.replace('on:click={', 'on:click|stopPropagation={')

    # Replace Settings Block
    stripped = line.strip()
    if '<div class="settings-details">' in line and not replaced_settings:
        skip_mode = True
        replaced_settings = True
        new_lines.append(settings_replacement)
        continue
    
    if skip_mode:
        if stripped == '</div>':
             # This assumes the first closing div after settings-details is the closing div for it.
             # Based on indentation in view_file, settings-details is at indentation 24.
             # Its closing div should also be at indentation 24.
             # But checking indentation is fragile if spaces vary.
             # However, we can look at the content.
             # The old content ends with </div> on a line by itself (indented).
             # Let's count indentation.
             indent = len(line) - len(line.lstrip())
             if indent == 24 or indent == 23: # slight leniency
                 skip_mode = False
             # If we are skipping, we don't append.
        continue

    new_lines.append(line)

with open(target_file, 'w') as f:
    f.writelines(new_lines)

print("Successfully updated App.svelte")
