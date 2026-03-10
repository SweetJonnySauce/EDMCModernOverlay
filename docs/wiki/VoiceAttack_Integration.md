# VoiceAttack and Modern Overlay Integration

The instructions below are intended to assist you with configuring VoiceAttack with the E:D Market Connector Modern Overlay plugin, utilizing the EDMCHotkeys plugin.

The EDMCHotkeys plugin listens for configured keybinds to perform available and chosen commands as hotkeys. We take this a step further by utilizing VoiceAttack to listen to voice commands to perform keystrokes which are used by the EDMCHotKeys plugin as actions, all without having to physically touch the keyboard.

<br/>

## Prerequisites 
[EDMCHotkeys](https://github.com/SweetJonnySauce/EDMCHotkeys) Plugin, Preinstalled  
[VoiceAttack](https://voiceattack.com/) (v2.x), Preinstalled

<br/>

## Configuration Steps
### E:D Market Connector
After you have installed the EDMCHotkeys plugin into the E:D Market Connector application, navigate to the E:D Market Connector settings screen located under **File, Settings**.

![E:D Market Connector Settings Menu](./images/VoiceAttack_Integration/edmc-settings-menu.png)

<br/>

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

![EDMCHotkeys Configuration Steps](./images/VoiceAttack_Integration/edmchotkeys-configuration-steps.png)

<hr/>


### VoiceAttack

<br/>

1. Load VoiceAttack and Click on the **More Profile Actions** button.
2. Select **Create New Profile**.

![VoiceAttack: Create New Profile. Steps 1-2](./images/VoiceAttack_Integration/voiceattack-create-new-profile-steps-1-2.png)

<br/>

<br/>

3. Choose a name to enter into the **Profile Name** field.
4. Click the **New Command** button.

![VoiceAttack: Add Profile. Steps 3-4](./images/VoiceAttack_Integration/voiceattack-add-profile-steps-3-4.png)

<br/>

<br/>

5. Ensure **When I say:** is **checked**, then enter the phrase you would like to say to activate the command, e.g. "Show Modern Overlay" or "Show Market Connector".

![VoiceAttack: Add a Command. Step 5](./images/VoiceAttack_Integration/voiceattack-add-a-command-step-5.png)

<br/>

<br/>

6. Click the **Key Press** button.
	- If the **Really important Key Press Tips - Please Read** message appears, click the **Close** button.

![VoiceAttack: Key Press. Step 6](./images/VoiceAttack_Integration/voiceattack-key-press-step-6.png)

<br/>

<br/>

7. Ensure the **Key capture** toggle is **enabled** (generally the default and blue when active). 
	- Note: Image capture could not accurately grab this example. 
8. **Press** the **keyboard key or key combination** that you want VoiceAttack to perform when it carries out the voice command.
9. Ensure the **Press and Release Key(s)** option is selected.
10. Click the **OK** button.

![VoiceAttack: Add a Key Press. Steps 7-10](./images/VoiceAttack_Integration/voiceattack-add-a-key-press-steps-7-10.png)

<br/>

<br/>

11. Click **Other >**, to add voice feedback after the voice command action has completed. 

![VoiceAttack: Add a Command, Other. Step 11](./images/VoiceAttack_Integration/voiceattack-add-a-command-other-step-11.png)

<br/>

<br/>

12. Click the **Sounds** flyout option.
13. Then click the **Say Something with Text-To-Speech** option.
	- You can be creative in the Sounds section, using built in system voices from a built-in text-to-speech engine or Play a Sound from pre-recorded audio clips that represent when the command has been recognized and executed. 

![VoiceAttack: Add a Command, Other, Sounds. Steps 12-13](./images/VoiceAttack_Integration/voiceattack-add-a-command-other-sounds-steps-12-13.png)

<br/>

<br/>

14. Enter the words or phrase you want to text-to-speech engine to say aloud, in the **text-to-speech** box, when the voice command action is performed, e.g. "Displaying E D Market Connectors Modern Overlay". 
15. Click the **OK** button.

![VoiceAttack: Say Something TTS. Steps 14-15](./images/VoiceAttack_Integration/voiceattack-say-something-tts-steps-14-15.png)

<br/>

<br/>

16. Enter descriptive text in the **Description** field, e.g. "Display the E:D Market Connector Modern Overlay".
17. Leave the **Send command to this target:**, **unchecked**. 
	- This defaults to the Active Window.
18. Click the **OK** button.
	- Repeat Steps 4-18 to add additional command action for coverage of:
		- Overlay On
		- Overlay Off
		- Launch Overlay Controller
			- Note: You can also duplicate commands quickly using alternate voice commands by right clicking an existing voice command and selecting, **Duplicate**.

![VoiceAttack: Command Description. Steps 16-18](./images/VoiceAttack_Integration/voiceattack-command-description-steps-16-18.png)

<br/>

<br/>

19. Click, **Done**, when you have completed adding or editing your voice commands and actions.

![VoiceAttack: Add Commands, Completed. Step 19](./images/VoiceAttack_Integration/voiceattack-add-commands-completed-step-19.png)

<br/>

<br/>

20. You are done at this stage if you are not using other VoiceAttack profiles or [HCS VOICEPACKS](https://www.hcsvoicepacks.com/collections/elite-dangerous) with Elite Dangerous.
	- Note: Ensure E:D Market Connector and VoiceAttack are running and your new VoiceAttack profile is loaded and in listening mode when playing Elite Dangerous.

![VoiceAttack: Profile Loaded and Listening.](./images/VoiceAttack_Integration/voiceattack-profile-loaded-and-listening.png)

<br/>

<br/>

 #### VoiceAttack with other Profiles
 <hr/>
If you are using VoiceAttack with other profiles such as, **HCS - Singularity (Elite Horizons/Odyssey LIVE)**, there are additional steps you must complete when using your customized voice commands simultaneously: 

<br/>

<br/>

1. **Switch** to your main Elite Dangerous profile, e.g. HCS - Singularity (Elite Horizons/Odyssey LIVE). 
2. Click the **Edit Profile** button. 

![VoiceAttack: Additional. Steps 1-2](./images/VoiceAttack_Integration/voiceattack-additional-steps-1-2.png)

<br/>

<br/>

3. Click the **Options** button, in the **Edit a Profile** window.

![VoiceAttack: Additional. Step 3](./images/VoiceAttack_Integration/voiceattack-additional-step-3.png)

<br/>

<br/>

4. Click the ellipsis button **...** to the right of the **Include commands from other profiles:** field, within the **Profile Options** tab, in the **Profile General** window.

![VoiceAttack: Additional. Step 4](./images/VoiceAttack_Integration/voiceattack-additional-step-4.png)

<br/>

<br/>

5. Click the **Plus** button, to add a profile to the list of included profiles.

![VoiceAttack: Additional. Step 5](./images/VoiceAttack_Integration/voiceattack-additional-step-5.png)

<br/>

<br/>

6. **Select** the profile you created above from the dropdown list to include, e.g. "EDMC".
7. Then click the **OK** button. 

![VoiceAttack: Additional. Steps 6-7](./images/VoiceAttack_Integration/voiceattack-additional-steps-6-7.png)

<br/>

<br/>

8. If necessary, reorder the list of included profiles, with the **Up** and **Down** arrows If you have more than one included profile in the list. 
	- Note: Higher profiles have higher priority.
9.  Then click the **OK** button.

![VoiceAttack: Additional. Steps 8-9](./images/VoiceAttack_Integration/voiceattack-additional-steps-8-9.png)

<br/>

<br/>

10. Click the **OK** button in the **Profile Options** window.

![VoiceAttack: Additional. Step 10](./images/VoiceAttack_Integration/voiceattack-additional-step-10.png)

<br/>

<br/>

11. Click the **Done** button in the **Edit a Profile** window.

![VoiceAttack: Additional. Step 11](./images/VoiceAttack_Integration/voiceattack-additional-step-11.png)

<br/>

<br/>

12. You are done combining your custom VoiceAttack profile with an existing profile. 
	- Note: Ensure E:D Market Connector and VoiceAttack are running and your new VoiceAttack profile is loaded and in listening mode when playing Elite Dangerous.

![VoiceAttack: Additional. Completed](./images/VoiceAttack_Integration/voiceattack-additional-completed.png)

<br/>

<br/>

## Tips and Considerations

1. Validate desired overlays for installed plugins are enabled.
2. Use easily understood and remembered voice commands for improved use and recognition.
3. Not all EDMCHotkeys keybind or keybind combinations will work with all operating systems and versions. These instruction were tested on Windows 11 24H2 x64 at the time of writing.
