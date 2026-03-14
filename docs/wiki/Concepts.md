Current status: WIP

In this wiki, we will cover some Overlay concepts to help you build your mental model of how the overlay works. Capitalized terms are defined below in the Terms section of this doc.


## What is EDMCModernOverlay
At a high level, EDMCModernOverlay is a plugin for EDMC. By itself, EDMCModernOverlay doesn't do anything to enrich the game experience. It does however act as a conduit for other Plugins to display on-screen messages (called Payloads). Without EDMCModernOverlay (or a legacy overlay), Plugins would need to handle any sort of on-screen display directly in their respective codebases.

## How are Payloads configured
Payloads are solely configured by the sending Plugin. Typically the Plugin developer will define at least Payload Name, X/Y placement, color, size, Time To Live (TTL), and information to display. 

## How do Payloads relate to Plugin Groups?
Plugin Groups is an EDMCModernOverlay concept and is not available on legacy Overlays. A Plugin Group is comprised of multiple payloads typed by the prefix of the Payload Name. For example, take the Payload Name `bgstally-msg-tick-0`. Breaking this down by prefixes, we have the following:

  - `bgstally-`: All Payloads with this Prefix belong to the Plugin "BGS-Tally"
  - `bgstally-msg-tick-`: All Payloads with this Prefix belong to the Plugin Group "BGS-Tally Tick" 
  - `bgstally-msg-tick-0`: This is one Payload, potentially among many, within the Plugin Group "BGS-Tally Tick"

Plugin Groups exist to handle everything from automatic scaling of Payloads (especially vector images) to providing a target used to set User Configurations

## How are Plugin Groups configured?
First off, Plugin Groups is unique to EDMCModernOverlay. There is no concept of a Plugin Group with legacy Overlays. With EDMCModernOverlay there are two types of configurations you will want to be aware of:
   1) Plugin Defined Configurations made by calling `define_plugin_group` at time of Plugin start-up. These settings are set once by the Plugin developer. There are a few settings available via Plugin Defined Configurations that are not available to CMDRs (e.g. `marker_label_position`)
   1) User (CMDR) Defined Configurations made at run time using the Overlay Controller. These settings allow for real time "in-game" configuration changes without having to touch code or settings. User Defined Configurations are effectively added on to Plugin defined configurations.

# Terms

## EDMC
The acronym for EDMarketConnector.

## Overlay
An EDMC plugin that handles the undifferentiated heavy lifting of displaying Payloads on-screen. EDMCModernOverlay, edmcoverlay, and edmcoverlay2 are examples of Overlay plugins.

## Overlay Controller
An "in game" real-time configuration utility that CMDRs can use to configure Plugin Groups without having to manually touch configuration files or individual Plugin settings.

## Payloads
An atomic message or shape that is sent to an Overlay to be displayed on screen. As of the writing of this wiki the types of Payloads available are text messages (`send_message`), rectangular shapes (`send_shape`), and vector images (`send_raw`)

## Payload Name
Every Payload sent to the Overlay has a name (`msgid` in the API calls). Plugins can then reference this name in subsequent Payloads to change what is being displayed or to clear the information being sent from the screen (either by sending a null string "" or a TTL of 0. EDMCModernOverlay provides advanced capabilities beyond what the legacy overlays provide by grouping like Payload Names. 

## Plugins
Any plugin other than the Overlay that sends Payloads to be displayed on-screen.

## Plugin Defined Configurations
Configurations made for a Plugin Group via an API call to `define_plugin_group`. These are stored in `overlay_groupings.json`. Only Plugin Developers need to worry about these configurations. If the Plugin Developer decides to manually update `overlay_groupings.json`, they will need to open up a PR against EDMCModernOverlay to make sure their configurations are shipped with the next release of the Overlay.

## Plugin Groups
A Plugin Group is a named grouping of Payloads as defined by Prefix Names

## Prefix Names
In the `define_plugin_group` API this maps to `plugin_group_name` (legacy alias: `id_prefix_group`). Prefix Names are the semantic part of the Payload Name and are used to group related Payloads into a Plugin Group.

## User (CMDR) Defined Configurations
Additive configurations made by CMDRs using the in-game Overlay Controller. These configurations are stored in `overlay_groupings.user.json` and Plugin Developers won't need to worry about these typically.
