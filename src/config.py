#!/usr/bin/env python

def generate(filename):
	with open(filename + '.sumocfg', 'w') as f:
		f.write('''<configuration>
    <input>
        <net-file value="{0}.net.xml"/>
        <route-files value="{0}.rou.xml"/>
        <gui-settings-file value="{0}.settings.xml"/>
    </input>

    <traci_server>
        <remote-port value="8813"/>
    </traci_server>
</configuration>'''.format(filename))

	with open(filename + '.settings.xml', 'w') as f:
		f.write('''<viewsettings>
    <viewport zoom="300"/>
    <delay value="100"/>
</viewsettings>''')