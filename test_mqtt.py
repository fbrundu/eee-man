import paho.mqtt.client as mqtt
import sys


# e.g. test.mosquitto.org
broker = sys.argv[1]


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, rc):
    print("Connected with result code " + str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("eee/sched/results")


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    # import ipdb; ipdb.set_trace()
    print("Topic:", msg.topic + "\nMessage:", str(msg.payload))

client = mqtt.Client("fakeclient", clean_session=False)
client.on_connect = on_connect
client.on_message = on_message

client.connect(broker, 1883, 60)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_forever()
