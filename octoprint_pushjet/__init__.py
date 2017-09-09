# coding=utf-8
from __future__ import absolute_import

import datetime
import threading
import time

import octoprint.plugin
import octoprint.util
import os
import requests


class PushjetPlugin(octoprint.plugin.SettingsPlugin,
                    octoprint.plugin.AssetPlugin,
                    octoprint.plugin.TemplatePlugin,
                    octoprint.plugin.EventHandlerPlugin):

    m70_cmd = ""

    def sent_m70(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
        if gcode and gcode == "M70":
            self.m70_cmd = cmd[3:]

    def PrintDone(self, payload):
        remove_ext = self._settings.get_boolean(['remove_ext'])
        file_name = self.get_filename(
                        payload,
                        remove_extension=remove_ext)
        elapsed_time_in_seconds = payload["time"]

        elapsed_time = octoprint.util.get_formatted_timedelta(
                                    datetime.timedelta(
                                        seconds=elapsed_time_in_seconds))

        # Create the message
        return self._settings.get(["events", "PrintDone", "message"]).format(
            **locals())

    def PrintFailed(self, payload):
        remove_ext = self._settings.get_boolean(['remove_ext'])
        file_name = self.get_filename(
                        payload,
                        remove_extension=remove_ext)
        return self._settings.get(["events", "PrintFailed", "message"]).format(
            **locals())

    def PrintPaused(self, payload):
        m70_cmd = ""
        if self.m70_cmd != "":
            m70_cmd = self.m70_cmd

        return self._settings.get(["events", "PrintPaused", "message"]).format(
                                                                    **locals())

    def Waiting(self, payload):
        return self.PrintPaused(payload)

    def PrintStarted(self, payload):
        self.m70_cmd = ""

    def on_event(self, event, payload):

        if payload is None:
            payload = {}
        try:
            # this check is necessary since some events are tuple
            if isinstance(event, str) and hasattr(self, event):
                payload["message"] = getattr(self, event)(payload)

                if self._settings.get_boolean(['timestamp']):
                    payload["message"] = self.append_time(payload["message"])
                self._logger.info("Event triggered: %s " % str(event))
        except AttributeError:
            return

        # Only continue when there is a priority (i.e not None)
        priority = self._settings.get(["events", event, "priority"])
        if priority:
            payload["priority"] = priority
            self.event_message(payload)

    def event_message(self, payload):

        url = self._settings.get(["api_url"])
        secret = self._settings.get(['token'])
        retry = self._settings.get_int(['retry'])
        sleep_time = self._settings.get_int(['time_retry'])
        # Bad but i cannot withstand too long names
        printer = self._printer_profile_manager.get_current_or_default

        title = "Octoprint"
        if self._printer_profile_manager is not None and "name" in printer():
            title += ": %s" % printer()["name"]

        # Send the message async
        try:
            thread = threading.Thread(target=self.send_message,
                                      args=(url,
                                            secret,
                                            title,
                                            payload["message"],
                                            payload["priority"],
                                            retry,
                                            sleep_time,)
                                      )
            thread.daemon = True
            thread.start()
        except Exception as e:
            self._logger.exception(str(e))

    def send_message(self, url, secret, title, message, level, retry, sleep):
        message_url = '/message'
        data = {
                'title': title,
                'message': message,
                'level': level,
                'secret': secret
                }

        for i in range(retry):
            try:
                r = requests.post(url + message_url, data=data).json()
                if "status" in r and r["status"] == "ok":
                    self._logger.info("Message successfully sent")
                    return
            except Exception:
                pass
            time.sleep(sleep)
        self._logger.info("Unable to send the message")

    def append_time(self, message):
        ts = time.time()
        st = datetime.datetime.fromtimestamp(ts).strftime('%H:%M')
        return "%s on %s" % (message, st)

    def get_filename(self, payload, remove_extension=True):
        file_name = os.path.basename(payload["file"])
        if remove_extension:
            file_name = file_name.rsplit('.', 1)[0]
        return file_name

    def get_settings_defaults(self):
        return dict(
            api_url="https://api.pushjet.io/",
            token="secret token here",
            retry=5,
            time_retry=10,
            timestamp=True,
            remove_ext=True,
            events=dict(
                PrintDone=dict(
                    name="Print done",
                    message="Print job finished: {file_name}, "
                            "finished printing in {elapsed_time}",
                    priority=1
                ),
                PrintFailed=dict(
                    name="Print failed",
                    message="Print job failed: {file_name}",
                    priority=1
                ),
                PrintPaused=dict(
                    name="Print paused",
                    help="Send a notification when a Pause event is received. "
                         "When a m70 was sent to the printer, "
                         "the message will be appended to the notification.",
                    message="Print job paused {m70_cmd}",
                    priority=1
                ),
                Waiting=dict(
                    name="Printer is waiting",
                    help="Send a notification when a Waiting event is "
                         "received. When a m70 was sent to the printer, "
                         "the message will be appended to the notification.",
                    message="Printer is waiting {m70_cmd}",
                    priority=1
                )
            )
        )

    def get_settings_restricted_paths(self):
        return dict(admin=[["token", "api_url"]])

    def get_assets(self):
        return dict()

    def get_template_configs(self):
        return [
            dict(type="settings", custom_bindings=False)
        ]

    def get_template_vars(self):
        return dict(
            events=self.get_settings_defaults()['events']
        )

    def get_update_information(self):
        return dict(
            pushjet=dict(
                displayName="Pushjet Plugin",
                displayVersion=self._plugin_version,

                # version check: github repository
                type="github_release",
                user="dipusone",
                repo="OctoPrint-Pushjet",
                current=self._plugin_version,

                # update method: pip
                pip="https://github.com/dipusone/OctoPrint-Pushjet/archive/{target_version}.zip"
            )
        )


__plugin_name__ = "Pushjet Plugin"


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = PushjetPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
        "octoprint.comm.protocol.gcode.sent": __plugin_implementation__.sent_m70
    }

