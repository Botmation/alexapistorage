# -*- coding: utf-8 -*-
from __future__ import print_function
import math
import string
import random
import time
import json

import boto3 #AWS library for pushing data to CLI to Raspberry PI
#Need to increase timeout from 3 seconds to 10 seconds.


SAYAS_INTERJECT = "<say-as interpret-as='interjection'>"
SAYAS_SPELLOUT = "<say-as interpret-as='spell-out'>"
SAYAS = "</say-as>"
BREAKSTRONG = "<break strength='strong'/>"
WELCOME_MESSAGE = "Welcome to the storage skill"


# --------------- entry point -----------------

def lambda_handler(event, context):
    """ App entry point  """
    
    if event['request']['type'] == "LaunchRequest":
        return on_launch()
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'])

def convert(dictionary):
    #Recursively converts dictionary keys to strings.
    if not isinstance(dictionary, dict):
        return dictionary
    return dict((str(k), convert(v)) 
        for k, v in dictionary.items())


# --------------- response handlers -----------------

def rpi_reply():
    #Read thing state for delta change from raspberry pi
    print('Reading response from Raspberry Pi')
    client = boto3.client('iot-data')
    #Delay initial poll to give pi time to respond to IOT
    time.sleep(1)
    for i in range(3):
        rpishadow = client.get_thing_shadow(thingName='alexa123thing')
        #Decode streaming body into json
        streamingBody = rpishadow["payload"]
        rpiresponse = json.loads(streamingBody.read())
        rpiresponse = convert(rpiresponse)

        if 'delta' in rpiresponse['state']:
            print(str(rpiresponse['state']['delta']['response']))
            #print(rpiresponse['state']['delta']['response'])
            if 'response' in rpiresponse['state']['delta']:
                print('Delta Received')
                #responsemsg = '{"state" : {"reported" : {"response" : "' + rpiresponse['state']['delta']['response'] + '"}}}'
                responsemsg = '{"state" : {"reported" : {"response" : "' + 'received' + '"}}}'
                response = client.update_thing_shadow(thingName='alexa123thing',payload=responsemsg)
                speechoutput = rpiresponse['state']['delta']['response']
                print(speechoutput)
                tora = {
                    'version': '1.0',
                    'response': {
                    'outputSpeech': {
                    'type': 'PlainText',
                    'text': speechoutput
                    }
                    }}
                return tora
        else:
            time.sleep(1)
            
def on_intent(request, session):
    """ Called on receipt of an Intent  """

    intent = request['intent']
    intent_name = request['intent']['name']

    print("on_intent " +intent_name)
    get_state(session)

    if 'dialogState' in request:
        #delegate to Alexa until dialog sequence is complete
        if request['dialogState'] == "STARTED" or request['dialogState'] == "IN_PROGRESS":
            return dialog_response("", False)

    # process the intents
    if intent_name == "alexastorageIntent":
        mycommand = intent['slots']['item']['value']
        print(mycommand)
        client = boto3.client('iot-data')
        #Create json message to send to raspberry pi
        rpidata = '{"state": {"desired" : {"lights" : "' + mycommand + '"}}}'

        # try update iot shadow and return response
        response = client.update_thing_shadow(thingName='alexa123thing',payload=rpidata)
        
        return rpi_reply()



    elif intent_name == "AMAZON.HelpIntent":
        return do_help()
    elif intent_name == "AMAZON.StopIntent":
        return do_stop()
    elif intent_name == "AMAZON.CancelIntent":
        return do_stop()
    elif intent_name == "AMAZON.StartoverIntent":
        return do_quiz(request)
    else:
        print("invalid intent reply with help")
        return do_help()


def do_stop():
    """  stop the app """

    attributes = {"state":globals()['STATE']}
    return response(attributes, response_plain_text(EXIT_SKILL_MESSAGE, True))

def do_help():
    """ return a help response  """

    global STATE
    STATE = STATE_START
    attributes = {"state":globals()['STATE']}
    return response(attributes, response_plain_text(HELP_MESSAGE, False))

def on_launch():
    """ called on Launch reply with a welcome message """
 
    return get_welcome_message()

def on_session_ended(request):
    """ called on session end  """

    if request['reason']:
        end_reason = request['reason']
        print("on_session_ended reason: " + end_reason)
    else:
        print("on_session_ended")



#will be useful for follow up type programs
def get_state(session):
    """ get and set the current state  """

    global STATE


# --------------- response string formatters -----------------



def get_badanswer(outtext):
    """ bad answer response """

    if outtext == "":
        outtext = "This"
    return ("I'm sorry. " +outtext +" is not something I know very "
            "much about in this skill. " +HELP_MESSAGE)



# --------------- speech response handlers -----------------
#  for details of Json format see:
#  https://developer.amazon.com/public/solutions/alexa/alexa-skills-kit/docs/alexa-skills-kit-interface-reference

def response_plain_text(output, endsession):
    """ create a simple json plain text response  """

    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'shouldEndSession': endsession
    }


def response_ssml_text(output, endsession):
    """ create a simple json plain text response  """

    return {
        'outputSpeech': {
            'type': 'SSML',
            'ssml': "<speak>" +output +"</speak>"
        },
        'shouldEndSession': endsession
    }

def response_ssml_text_and_prompt(output, endsession, reprompt_text):
    """ create a Ssml response with prompt  """

    return {
        'outputSpeech': {
            'type': 'SSML',
            'ssml': "<speak>" +output +"</speak>"
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'SSML',
                'ssml': "<speak>" +reprompt_text +"</speak>"
            }
        },
        'shouldEndSession': endsession
    }


def response_ssml_cardimage_prompt(title, output, endsession, cardtext, abbreviation, reprompt):
    """ create a simple json plain text response  """

    smallimage = get_smallimage(abbreviation)
    largeimage = get_largeimage(abbreviation)
    return {
        'card': {
            'type': 'Standard',
            'title': title,
            'text': cardtext,
            'image':{
                'smallimageurl':smallimage,
                'largeimageurl':largeimage
            },
        },
        'outputSpeech': {
            'type': 'SSML',
            'ssml': "<speak>" +output +"</speak>"
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'SSML',
                'ssml': "<speak>" +reprompt +"</speak>"
            }
        },
        'shouldEndSession': endsession
    }

def response_ssml_text_reprompt(output, endsession, reprompt_text):
    """  create a simple json response with a card  """

    return {
        'outputSpeech': {
            'type': 'SSML',
            'ssml': "<speak>" +output +"</speak>"
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'SSML',
                'ssml': "<speak>" +reprompt_text +"</speak>"
            }
        },
        'shouldEndSession': endsession
    }

def dialog_response(attributes, endsession):
    """  create a simple json response with card """

    return {
        'version': '1.0',
        'sessionAttributes': attributes,
        'response':{
            'directives': [
                {
                    'type': 'Dialog.Delegate'
                }
            ],
            'shouldEndSession': endsession
        }
    }

def response(attributes, speech_response):
    """ create a simple json response """

    return {
        'version': '1.0',
        'sessionAttributes': attributes,
        'response': speech_response
}
