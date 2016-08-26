#! /usr/bin/env python
import argparse
import requests
import json
import time

def uptime_formatter(uptime):
    # Helper vars:
     MINUTE  = 60
     HOUR    = MINUTE * 60
     DAY     = HOUR * 24
 
     # Get the days, hours, etc:
     days    = int( uptime / DAY )
     hours   = int( ( uptime % DAY ) / HOUR )
     minutes = int( ( uptime % HOUR ) / MINUTE )
     seconds = int( uptime % MINUTE )
 
     # Build up the pretty string (like this: "N days, N hours, N minutes, N seconds")
     string = ""
     if days > 0:
         string += str(days) + " " + (days == 1 and "day" or "days" ) + ", "
     if len(string) > 0 or hours > 0:
         string += str(hours) + " " + (hours == 1 and "hour" or "hours" ) + ", "
     if len(string) > 0 or minutes > 0:
         string += str(minutes) + " " + (minutes == 1 and "minute" or "minutes" ) + ", "
     string += str(seconds) + " " + (seconds == 1 and "second" or "seconds" )
 
     return string

def main():
    """
    This function prints out the current agent configuration file.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", help="the port number to connect to")
    args = parser.parse_args()

    port = args.port or 8089

    try:
        r = requests.get('http://localhost:%s/status/' % port)
        data = r.json()
        print('AgentStat:')
        print('---------')
        print('Agent Version:      %s' % data['agent_version'])
        print('Supervisor Version: %s' % data['supervisor_version'])
        print('Uptime:             %s' % uptime_formatter(time.time() - data['start_time']))
        print('Sample interval:    %s' % uptime_formatter(int(data['sample_interval'])))
        print('Push interval:      %s' % uptime_formatter(int(data['push_interval'])))
        print('Log level:          %s' % data['log_level'])
        print('Log file:           %s' % data['log_file'])
        print('Database:           %s' % data['database'])
        print('Token:              %s' % data['token'])
        print('URL:                %s' % data['url'])
        print('Port:               %s' % data['port'])
    except Exception as e:
        print('e: %s' % e)
        print('AgentStat: could not connect to agent on port %s.' % port)


if __name__ == "__main__":
    main()