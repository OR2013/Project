#!/usr/bin/env python

import os, sys
import optparse
import subprocess
import random
import config
import graph

# we need to import python modules from the $SUMO_HOME/tools directory
try:
    os.environ["SUMO_HOME"] = "/usr/share/sumo"
    sys.path.append(os.path.join(os.environ["SUMO_HOME"], "tools"))
    from sumolib import checkBinary
except ImportError:
    sys.exit("please declare environment variable 'SUMO_HOME' as the root directory of your sumo installation (it should contain folders 'bin', 'tools' and 'docs')")

import traci
# the port used for communicating with your sumo instance
PORT = 8813

def get_costs(edges):
    costs = {}
    for edge in edges:
        costs[edge] = traci.edge.getTraveltime(edge.encode('utf-8'))
    return costs

def change_edge_speed(edgesPoll, edges, speedChanges):
    if len(edgesPoll) == 0:
        edgesPoll = list(edges)
    edge = random.choice(edgesPoll)
    edgesPoll.remove(edge)
    speed = random.choice(range(1,100))
    speedChanges.append((edge.encode('utf-8'), speed))
    #print 'edge: {0}, speed: {1}'.format(edge, speed)
    traci.edge.setMaxSpeed(edge.encode('utf-8'), speed)

def run(edges, connections, speedChanges, optimalization, nogui):
    '''execute the TraCI control loop'''
    traci.init(PORT)
    if not nogui:
        traci.gui.trackVehicle('View #0', '0')
    #print 'route: {0}'.format(traci.vehicle.getRoute('0'))
    destination = traci.vehicle.getRoute('0')[-1]
    edgesPoll = list(edges)

    time = traci.simulation.getCurrentTime()
    while traci.simulation.getMinExpectedNumber() > 0:
        if optimalization:
            change_edge_speed(edgesPoll, edges, speedChanges)
            edge = traci.vehicle.getRoadID('0')
            if edge in edges and traci.vehicle.getLanePosition('0') >= 0.9 * traci.lane.getLength(traci.vehicle.getLaneID('0')):
                shortestPath = graph.dijkstra(edge, destination, edges, get_costs(edges), connections)
                #print 'dijkstra: {0}'.format(shortestPath)
                traci.vehicle.setRoute('0', shortestPath)
        else:
            if len(speedChanges) > 0:
                edge, speed = speedChanges.pop()
                traci.edge.setMaxSpeed(edge, speed)
            else:
                change_edge_speed(edgesPoll, edges, [])
        traci.simulationStep()
    time = traci.simulation.getCurrentTime() - time
    traci.close()
    sys.stdout.flush()
    return time

def get_options():
    optParser = optparse.OptionParser()
    optParser.add_option('--nogui', action='store_true', default=False, help='run the commandline version of sumo')
    optParser.add_option('--nogen', action='store_true', default=False, help='run without road network generation')
    optParser.add_option('-p', '--prefix', dest='prefix', default='random', help='files names prefix')
    optParser.add_option('-s', '--size', dest='size', default='10', help='road network size')
    options, args = optParser.parse_args()
    return options

# this is the main entry point of this script
if __name__ == '__main__':
    options = get_options()

    options.prefix = '../config/' + options.prefix

    # this script has been called from the command line. It will start sumo as a
    # server, then connect and run
    if options.nogui:
        sumoBinary = checkBinary('sumo')
    else:
        sumoBinary = checkBinary('sumo-gui')

    # this is the normal way of using traci. sumo is started as a
    # subprocess and then the python script connects and runs

    if not options.nogen:
        print 'Generating road network...'
        subprocess.Popen(['netgenerate', '--rand', '--random', 'true', '--rand.iterations', options.size, '--rand.max-distance', '500', '--no-turnarounds', 'true', '-o', options.prefix+'.net.xml'], stdout=sys.stdout, stderr=sys.stderr).wait()

    print 'Reading edges...'
    edges = graph.read_edges(options.prefix + '.net.xml')
    print 'Success.'

    print 'Reading edge connections...'
    connections = graph.read_connections(options.prefix + '.net.xml')
    print 'Success.'

    if not options.nogen:
        print 'Generating route...'
        subprocess.Popen(['python', os.path.join(os.environ['SUMO_HOME'], 'tools/trip/randomTrips.py'), '-e', '1', '-n', options.prefix+'.net.xml', '-r', options.prefix+'.rou.xml', '-o', options.prefix+'.trips.xml', '--fringe-factor', '1000000'], stdout=sys.stdout, stderr=sys.stderr).wait()
        print 'Success.'

        print 'Writing configuration...'
        config.generate(options.prefix)
        print 'Success.'

    speedChanges = []
    sumoProcess = subprocess.Popen([sumoBinary, '-c', options.prefix + '.sumocfg'], stdout=sys.stdout, stderr=sys.stderr)
    optTime = run(edges, connections, speedChanges, True, options.nogui)
    sumoProcess.wait()

    speedChanges.reverse()
    sumoProcess = subprocess.Popen([sumoBinary, '-c', options.prefix + '.sumocfg'], stdout=sys.stdout, stderr=sys.stderr)
    noOptTime = run(edges, connections, speedChanges, False, options.nogui)
    sumoProcess.wait()

    print '\nSimulation time with optimalization: {0}'.format(optTime / 1000.)
    print 'Simulation time without optimalization: {0}'.format(noOptTime / 1000.)
