# -*- coding: utf-8 -*-
# @Author: Matt Pedler
# @Date:   2017-05-12 10:16:15
# @Last Modified by:   Matt Pedler
# @Last Modified time: 2017-10-27 13:14:18
import socket
from kivy.logger import Logger


class NetconnectdClient():
    address = '/var/run/netconnectd.sock'
    timeout = 120

    def hostname(self):
        return socket.gethostname() + ".local"

    def get_ip(self):
        return [l for l in ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1], [[(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) if l][0][0]

    def _send_message(self, message, data):
        obj = dict()
        obj[message] = data

        import json
        js = json.dumps(obj, encoding="utf8", separators=(",", ":"))

        import socket
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        try:
            sock.connect(self.address)
            sock.sendall(js + '\x00')

            buffer = []
            while True:
                chunk = sock.recv(16)
                if chunk:
                    buffer.append(chunk)
                    if chunk.endswith('\x00'):
                        break

            data = ''.join(buffer).strip()[:-1]

            response = json.loads(data.strip())
            if "result" in response:
                return True, response["result"]

            elif "error" in response:
                # something went wrong
                Logger.info(
                    "Request to netconnectd went wrong: " + response["error"])
                return False, response["error"]

            else:
                output = "Unknown response from netconnectd: {response!r}".format(
                    response=response)
                Logger.info(output)
                return False, output

        except Exception as e:
            output = "Error while talking to netconnectd: {}".format(e.message)
            Logger.info(output)
            return False, output

        finally:
            sock.close()

    def _get_wifi_list(self, force=False):
        payload = dict()
        if force:
            Logger.info("Forcing wifi refresh...")
            payload["force"] = True

        flag, content = self._send_message("list_wifi", payload)
        if not flag:
            raise RuntimeError("Error while listing wifi: " + content)

        result = []
        for wifi in content:
            result.append(dict(ssid=wifi["ssid"], address=wifi["address"], quality=wifi[
                "signal"], encrypted=wifi["encrypted"]))
        Logger.info('Wifi: {}'.format(result))
        return result

    def _get_status(self):
        payload = dict()
        flag, content = self._send_message("status", payload)
        if not flag:
            raise RuntimeError("Error while querying status: " + content)

        return content

    def _configure_and_select_wifi(self, ssid, psk, force=False):
        payload = dict(
            ssid=ssid,
            psk=psk,
            force=force
        )

        flag, content = self._send_message("config_wifi", payload)
        if not flag:
            raise RuntimeError("Error while configuring wifi: " + content)

        flag, content = self._send_message("start_wifi", dict())
        if not flag:
            raise RuntimeError("Error while selecting wifi: " + content)

    def _forget_wifi(self):
        payload = dict()
        flag, content = self._send_message("forget_wifi", payload)
        if not flag:
            raise RuntimeError("Error while forgetting wifi: " + content)

    def _reset(self):
        payload = dict()
        flag, content = self._send_message("reset", payload)
        if not flag:
            raise RuntimeError(
                "Error while factory resetting netconnectd: " + content)

    def _start_ap(self):
        payload = dict()
        flag, content = self._send_message("start_ap", payload)
        if not flag:
            raise RuntimeError("Error while starting ap: " + content)

    def _stop_ap(self):
        payload = dict()
        flag, content = self._send_message("stop_ap", payload)
        if not flag:
            raise RuntimeError("Error while stopping ap: " + content)

    def command(self, command, data):
        if command == "configure_wifi":
            self._configure_and_select_wifi(data["ssid"], data["psk"],
                                            force=data["force"] if "force" in data else False)
        elif command == "forget_wifi":
            self._forget_wifi()
        elif command == "reset":
            self._reset()
        elif command == "start_ap":
            self._start_ap()
        elif command == "stop_ap":
            self._stop_ap()
        elif command == 'list_wifi':
            return self._get_wifi_list(force=True)

        return
