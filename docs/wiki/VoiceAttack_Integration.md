# DRAFT (Fixing images in prep for PR) VoiceAttack and Modern Overlay Integration

The instructions below are intended to assist you with configuring VoiceAttack with the E:D Market Connector Modern Overlay plugin, utilizing the EDMCHotkeys plugin.

The EDMCHotkeys plugin listens for configured keybinds to perform available and chosen commands as hotkeys. We take this a step further by utilizing VoiceAttack to listen to voice commands to perform keystrokes which are used by the EDMCHotKeys plugin as actions, all without having to physically touch the keyboard.

## Prerequisites 
[EDMCHotkeys](https://github.com/SweetJonnySauce/EDMCHotkeys) Plugin, Preinstalled  
[VoiceAttack](https://voiceattack.com/) (v2.x), Preinstalled


## Configuration Steps
### E:D Market Connector
After you have installed the EDMCHotkeys plugin into the E:D Market Connector application, navigate to the E:D Market Connector settings screen located under **File, Settings**.

![E:D Market Connector Settings Menu](./images/VoiceAttack_Integration/edmc-settings-menu.png)

<hr/>

***EDMCHotkeys Plugin Screen***
1. Click the **Add Binding** button to add a new Hotkey action.
2. Click within the Hotkey field.
	- Using your keyboard, press the key combination you want to use for your first action.
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

1. Load VoiceAttack and Click on the **More Profile Actions** button.
2. Select **Create New Profile**.

<img width="839" height="152" alt="VoiceAttack: Create New Profile. Steps 1-2" src="https://github.com/user-attachments/assets/321b5fd8-2480-4a6e-ba70-08de9c246621" />



3. Choose a name to enter into the **Profile Name** field.
4. Click the **New Command** button.

<img width="1086" height="505" alt="VoiceAttack: Add Profile. Steps 3-4" src="https://github.com/user-attachments/assets/2fa842ed-d16b-4be2-8c86-cbc6c2d92532" />



5. Ensure **When I say:** is **checked**, then enter the phrase you would like to say to activate the command, e.g. "Show Modern Overlay" or "Show Market Connector".


<img width="988" height="221" alt="VoiceAttack: Add a Command. Step 5" src="https://github.com/user-attachments/assets/39f1e287-1313-4e15-aff2-a9c204eeeb65" />


6. Click the **Key Press** button.
	- If the **Really important Key Press Tips - Please Read** message appears, click the **Close** button.

<img width="440" height="293" alt="VoiceAttack: Key Press. Step 6" src="https://github.com/user-attachments/assets/47a5a4f6-d2db-4358-9429-bf2e546b1553" />



7. Ensure the **Key capture** toggle is **enabled** (generally the default and blue when active). 
	- Note: Image capture could not accurately grab this example. 
8. **Press** the **keyboard key or key combination** that you want VoiceAttack to perform when it carries out the voice command.
9. Ensure the **Press and Release Key(s)** option is selected.
10. Click the **OK** button.

<img width="512" height="584" alt="VoiceAttack: Add a Key Press. Steps 7-10" src="https://github.com/user-attachments/assets/0064f50a-15b9-4866-92c9-deb495a7a74f" />



11. Click **Other >**, to add voice feedback after the voice command action has completed. 

<img width="424" height="398" alt="VoiceAttack: Add a Command, Other. Step 11" src="https://github.com/user-attachments/assets/4b2f006b-e4f4-4256-b83e-f9eea0583815" />



12. Click the **Sounds** flyout option.
13. Then click the **Say Something with Text-To-Speech** option.
	- You can be creative in the Sounds section, using built in system voices from a built-in text-to-speech engine or Play a Sound from pre-recorded audio clips that represent when the command has been recognized and executed. 

<img width="707" height="338" alt="VoiceAttack: Add a Command, Other, Sounds. Steps 12-13" src="https://github.com/user-attachments/assets/df0c4351-ad5f-4922-ac7e-9ca73af874b3" />



14. Enter the words or phrase you want to text-to-speech engine to say aloud, in the **text-to-speech** box, when the voice command action is performed, e.g. "Displaying E D Market Connectors Modern Overlay". 
15. Click the **OK** button.

<img width="962" height="722" alt="VoiceAttack: Say Something TTS. Steps 14-15" src="https://github.com/user-attachments/assets/62f6e272-2106-4c0a-b09c-04941499d066" />



16. Enter descriptive text in the **Description** field, e.g. "Display the E:D Market Connector Modern Overlay".
17. Leave the **Send command to this target:**, **unchecked**. 
	- This defaults to the Active Window.
18. Click the **OK** button.
	- Repeat Steps 4-18 to add additional command action for coverage of:
		- Overlay On
		- Overlay Off
		- Launch Overlay Controller
			- Note: You can also duplicate commands quickly using alternate voice commands by right clicking an existing voice command and selecting, **Duplicate**.

<img width="982" height="715" alt="VoiceAttack: Command Description. Steps 16-18" src="https://github.com/user-attachments/assets/4929d435-77d1-4f84-90b5-162174c27755" />



19. Click, **Done**, when you have completed adding or editing your voice commands and actions.

<img width="1085" height="468" alt="VoiceAttack: Add Commands, Completed. Step 19" src="https://github.com/user-attachments/assets/13848dc0-8e6c-42c6-92f7-1774fc1819e9" />



20. You are done at this stage if you are not using other VoiceAttack profiles or [HCS VOICEPACKS](https://www.hcsvoicepacks.com/collections/elite-dangerous) with Elite Dangerous.
	- Note: Ensure E:D Market Connector and VoiceAttack are running and your new VoiceAttack profile is loaded and in listening mode when playing Elite Dangerous.

<img width="787" height="197" alt="VoiceAttack: Profile Loaded and Listening." src="https://github.com/user-attachments/assets/01af494a-9311-4ad7-addd-b7cc2bd01abf" />



 #### VoiceAttack with other Profiles
 <hr/>
If you are using VoiceAttack with other profiles such as, **HCS - Singularity (Elite Horizons/Odyssey LIVE)**, there are additional steps you must complete when using your customized voice commands simultaneously: 

1. **Switch** to your main Elite Dangerous profile, e.g. HCS - Singularity (Elite Horizons/Odyssey LIVE). 
2. Click the **Edit Profile** button. 

<img width="788" height="157" alt="VoiceAttack: Additional. Steps 1-2" src="https://github.com/user-attachments/assets/3a9a06e6-c1a6-4fe5-a60d-b47950eaf5bc" />



3. Click the **Options** button, in the **Edit a Profile** window.

<img width="516" height="196" alt="VoiceAttack: Additional. Step 3" src="https://github.com/user-attachments/assets/ecaf7614-b9bb-4b65-9df7-ac5ae504f7f1" />



4. Click the ellipsis button **...** to the right of the **Include commands from other profiles:** field, within the **Profile Options** tab, in the **Profile General** window.

<img width="647" height="657" alt="VoiceAttack: Additional. Step 4" src="https://github.com/user-attachments/assets/332034c2-c584-432d-a3e6-a29b878060ec" />



5. Click the **Plus** button, to add a profile to the list of included profiles.

<img width="674" height="523" alt="VoiceAttack: Additional. Step 5" src="https://github.com/user-attachments/assets/a7a88271-ac63-42a2-861b-def2d6c1df5b" />



6. **Select** the profile you created above from the dropdown list to include, e.g. "EDMC".
7. Then click the **OK** button. 

<img width="554" height="184" alt="VoiceAttack: Additional. Steps 6-7" src="https://github.com/user-attachments/assets/4f0b58c7-c1da-4592-ba8a-7bf13e3b9130" />



8. If necessary, reorder the list of included profiles, with the **Up** and **Down** arrows If you have more than one included profile in the list. 
	- Note: Higher profiles have higher priority.
9.  Then click the **OK** button.

<img width="675" height="524" alt="VoiceAttack: Additional. Steps 8-9" src="https://github.com/user-attachments/assets/5dee4084-2ed1-4476-ad98-c51cc4f8c728" />



10. Click the **OK** button in the **Profile Options** window.

<img width="648" height="660" alt="VoiceAttack: Additional. Step 10" src="https://github.com/user-attachments/assets/2fdf08bd-f51e-4ccb-8808-55e05ff14bf4" />



11. Click the **Done** button in the **Edit a Profile** window.

<img width="1086" height="508" alt="VoiceAttack: Additional. Step 11" src="https://github.com/user-attachments/assets/4f5e5403-33ac-4680-8138-ba87a100e4c2" />



12. You are done combining your custom VoiceAttack profile with an existing profile. 
	- Note: Ensure E:D Market Connector and VoiceAttack are running and your new VoiceAttack profile is loaded and in listening mode when playing Elite Dangerous.

<img width="1033" height="191" alt="VoiceAttack: Additional. Completed" src="https://github.com/user-attachments/assets/0f4e86f7-779f-4c7f-9590-642b11102a56" />



## Tips and Considerations

1. Validate desired overlays for installed plugins are enabled.
2. Use easily understood and remembered voice commands for improved use and recognition.
3. Not all EDMCHotkeys keybind or keybind combinations will work with all operating systems and versions. These instruction were tested on Windows 11 24H2 x64 at the time of writing.
