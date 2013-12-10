#!/usr/bin/env python

import os, sys
import re
from collections import defaultdict
from heapq import *

INFINITY = 1000000

try:
    os.environ["SUMO_HOME"] = "/usr/share/sumo"
    sys.path.append(os.path.join(os.environ["SUMO_HOME"], "tools"))
    from sumolib import checkBinary
except (ImportError, AttributeError):
    sys.exit("please declare environment variable 'SUMO_HOME' as the root directory of your sumo installation (it should contain folders 'bin', 'tools' and 'docs')")

import sumolib.net

def read_edges(netfile):
	edges = []
	for edge in sumolib.net.readNet(netfile)._edges:
		edges.append(edge._id)
	return edges

def read_lengths(netfile):
	lengths = {}
	for edge in sumolib.net.readNet(netfile)._edges:
		lengths[edge._id] = edge._length
	return lengths

def read_connections(netfile):
	connections = defaultdict(list)
	with open(netfile, 'r') as f:
		content = f.read()
		pattern = re.compile(r'<connection from="(-?\d+)" to="(-?\d+)".*?/>')
    	iterator = pattern.finditer(content)
    	for match in iterator:
    		connections[match.group(1)].append(match.group(2))
	return connections

def reverse_edge(edge):
	return str(-int(edge))

def furthest_edge(source, edges, connections, visited):
	dist = {}
	for edge in edges:
		dist[edge] = 0

	stack = [source]
	visited.add(source)
	while len(stack) > 0:
		edge = stack.pop()
		for neighbour in connections[edge]:
			if dist[neighbour] == 0:
				dist[neighbour] = dist[edge] + 1
				dist[reverse_edge(neighbour)] = dist[edge] + 1
				stack.append(neighbour)
				visited.add(neighbour)

	destination = max(dist, key=dist.get)
	return (destination, dist[destination], visited)

def get_distance(edges, connections):
	visited = set()
	distance = 0
	for edge in edges:
		if edge not in visited:
			s, _, visited = furthest_edge(edge, edges, connections, visited)
			d, dist, _ = furthest_edge(reverse_edge(s), edges, connections, set())
			print 'edge: {0}, source: {1}, dest: {2}, dist: {3}'.format(edge, s, d, dist)
			print 'visited: {0}'.format(visited)
			if dist > distance:
				source = s
				destination = d
				distance = dist
	return (source, destination)

def dijkstra(source, destination, edges, costs, connections):
	heap = []
	prev = {}
	dist = {}
	for edge in edges:
		if edge != source:
			heappush(heap, (INFINITY, edge))
			dist[edge] = INFINITY
			prev[edge] = 'undef'
	heappush(heap, (0, source))
	prev[source] = 'undef'
	dist[source] = 0

	while len(heap) > 0:
		cost, edge = heappop(heap)
		for neighbour in connections[edge]:
			if dist[neighbour] > dist[edge] + costs[neighbour]:
				dist[neighbour] = dist[edge] + costs[neighbour]
				prev[neighbour] = edge
				heappush(heap, (dist[neighbour], neighbour))

	edge = destination
	route = [edge]
	while prev[edge] != 'undef':
		edge = prev[edge]
		route.append(edge)
	route.reverse()
	return route