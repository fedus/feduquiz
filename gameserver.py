"""Game server (MQTT based)."""

from kivy.event import EventDispatcher
from kivy.clock import mainthread
from functools import partial

from auth import MQTT_CONF

import logging
import paho.mqtt.client as mqtt

LOG = logging.getLogger(__name__)

class MQTTGameServer(EventDispatcher):
    """MQTT Client."""

    def __init__(self, trivia):
        """Construct the MQTT client."""
        self._trivia = trivia
        self._client = None
        self.conf = MQTT_CONF
        self.start_client()
        self._code = None
        self._callback_subscriptions = []

    def listen(self, code):
        """Listen for game."""
        self.unsubscribe_all()
        self._code = code
        self._game_topic = '{}/{}/'.format(MQTT_CONF['base_topic'], code)
        self.basic_subscribe()

    def basic_subscribe(self):
        """Starts new game server with given code."""
        self.subscribe_and_callback(self.append_to_game_topic('joining/#'), self.on_player_join)
        self._trivia.bind(current_state=lambda widget, new_state: self.send(self.append_to_game_topic('state'), new_state.name, True))

    def unsubscribe_all(self):
        """Unsubscribe to all topics subscribed through subscribe_and_callback."""
        for subscription in self._callback_subscriptions:
            self._client.message_callback_remove(subscription)
        self._callback_subscriptions = []

    def subscribe_and_callback(self, topic, callback):
        self._client.subscribe(topic, 0)
        self._client.message_callback_add(topic, callback)
        self._callback_subscriptions.append(topic)

    @mainthread
    def on_player_join(self, client, userdata, message):
        """Handle player join attempts."""
        player_id = message.topic.split('/')[-1]
        player_name = str(message.payload.decode('utf8'))
        player = self._trivia.add_player(player_name, player_id)
        if player:
            player_callback = partial(self.on_player_answer, player)
            self.subscribe_and_callback(self.get_player_topic(player_id, 'input', '#'), player_callback)
            self.send(self.get_player_topic(player_id, 'status', 'join'), 'ack')
        else:
            self.send(self.get_player_topic(player_id, 'status', 'join'), 'nack')

    def register_player_callbacks(self, player):
        """Registers player callbacks."""
        send_to_player = partial(self.send, self.get_player_topic(player.id, 'status', 'answer'))
        player.bind(on_correct_answer=send_to_player('correct'))
        player.bind(on_incorrect_answer=send_to_player('incorrect'))
        player.bind(on_already_answered=send_to_player('already_answered'))
        player.bind(on_not_accepted=send_to_player('not_accepted'))
        player.bind(on_timed_out=send_to_player('timed_out'))

    def on_player_answer(self, player, client, userdata, message):
        """Handle player's answer."""
        answer = message.payload.decode('utf8')
        print('Answer received for player {}: {}'.format(player, answer))
        player.answer(answer)

    def start_client(self):
        """Connect to the MQTT server."""
        conf = self.conf
        LOG.info('Connecting to MQTT server at %s', conf['broker'])
        self._client = mqtt.Client(conf['client_id'], conf['protocol'])
        self._client.on_connect = self.on_connect
        if conf.get('username'):
            self._client.username_pw_set(conf['username'], conf['password'])
        if conf.get('certificate'):
            self._client.tls_set(conf['certificate'])
        self._client.connect(conf['broker'], conf['port'], conf['keepalive'])
        self._client.loop_start()

    def on_connect(self, client, userdata, flags, rc):  # pylint: disable=unused-argument, invalid-name
        """Do callback for when MQTT server connects."""
        LOG.info("Connected with result code %d", rc)

    def send(self, topic, payload, retain=False):
        """Sends the provided topic-payload pair."""
        LOG.debug("===> Sending %s to %s", str(payload), topic)
        self._client.publish(topic, payload, retain)

    def stop_client(self):
        """End the MQTT connection."""
        self._client.loop_stop()

    def append_to_game_topic(self, topic):
        """Append provided topic to game topic."""
        return '{}{}'.format(self._game_topic, topic)

    def get_player_topic(self, player_id, realm, suffix=None):
        """Returns the topic for a given player id."""
        evaluated_suffix = '/{}'.format(suffix) if suffix else ''
        return self.append_to_game_topic('players/{}/{}{}'.format(player_id, realm, evaluated_suffix))