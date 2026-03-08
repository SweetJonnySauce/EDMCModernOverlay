# DRAFT VoiceAttack and Modern Overlay Integration

The instructions below are intended to assist you with configuring VoiceAttack with the E:D Market Connector Modern Overlay plugin, utilizing the EDMCHotkeys plugin.

The EDMCHotkeys plugin listens for configured keybinds to perform available and chosen commands as hotkeys. We take this a step further by utilizing VoiceAttack to listen to voice commands to perform keystrokes which are used by the EDMCHotKeys plugin as actions, all without having to physically touch the keyboard.

## Prerequisites 
[EDMCHotkeys](https://github.com/SweetJonnySauce/EDMCHotkeys) Plugin, Preinstalled  
[VoiceAttack](https://voiceattack.com/) (v2.x), Preinstalled


## Configuration Steps
### E:D Market Connector
After you have installed the EDMCHotkeys plugin into the E:D Market Connector application, navigate to the E:D Market Connector settings screen located under **File, Settings**.

<img width="223" height="141" alt="E:D Market Connector Settings Menu" src="https://github.com/user-attachments/assets/bd109539-9bac-4fb6-8c14-e4ef716f08d5" />
<hr/>

*EDMCHotkeys Plugin Screen*
1. Click the **Add Binding** button to add a new Hotkey action.
2. Click within the Hotkey field.
	- Using your keyboard, press the key combination you want to use to for your first action.
		- This key combination will be detected and input into the field, in the order it understands.
		 - Some operating systems may not have all the keys detected properly. You may have to choose other key combinations to adjust for this.
		 - Ensure you do **not** use keybinds already in use by **Elite Dangerous** or other game tools.
3. Select the **EDMCModernOverlay** from the Plugin dropdown menu.
4. Select an action that you want to use with the Hotkey from the **Action** drop down menu.
5. Ensure the **Enabled** option is **Yes**.
	- Repeat Steps 1 - 5 to create desired bindings for each of the action options:
		- Overlay On
		- Overlay Off
		- Launch Overlay Controller
8. Click, **OK** to save and close the settings screen.

<img width="821" height="434" alt="EDMCHotkeys Configuration Steps" src="https://github.com/user-attachments/assets/9699ae32-3ccf-467f-b458-28d41f185d91" />

<hr/>


### VoiceAttack

#### Step 1:

 1 <img width="1085" height="140" alt="Screenshot 2026-03-06 192755" src="https://github.com/user-attachments/assets/3ea58fff-58de-415b-823c-89eafceafa6b" />


## Tips and Considerations

1. Validate desired overlays for installed plugins are enabled.
2. Attaching overlays to VR controllers allows for physical placement of the overlay canvas.
3. Use easily understood and remembered voice commands for improved use and recognition.
4. Not all EDMCHotkeys keybind or keybind combinations will work with all operating systems and versions. This instruction was testing on Windows 11 24H2 x64 at the time of writing.
