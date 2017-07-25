#!/usr/bin/env python3
# -*- coding: utf-8 -*-  
import sqlite3
import os
import sys
import traceback

from .common import open_database
from .get_path import get_path_unchecked
from ..common import Tintin
from ..common import logger

TRAVERSE_WEIGHT = "1,-1,1,-1,-1,1,1,1"
def traverse_bfs(conn, roomno, location=None):
    traverse_path = []
    stack = [(roomno,"NULL")]
    visited = set()
    last_room_no = roomno
    if location == None:
        bfs_max_count = 10
    else:
        bfs_max_count = 50
        
    while len(stack) != 0:
        bfs_max_count = bfs_max_count-1
        if bfs_max_count<0:
            break
        
        (dst_room_no,dst_room_name) = stack.pop(0)

        if location == None or dst_room_name == location:
            if last_room_no != dst_room_no:
                traverse_path.extend(get_path_unchecked(conn, last_room_no, dst_room_no,TRAVERSE_WEIGHT))
                last_room_no = dst_room_no
            
        visited.add(dst_room_no)

        sql = "select dst_room_no, dst_room_name from room_and_entrance where src_room_no = %d and is_boundary = 0" % (dst_room_no)

        for row in conn.execute(sql).fetchall():
            if row[0] not in visited:
                stack.append((row[0],row[1]))

    traverse_path.extend(get_path_unchecked(conn, last_room_no, roomno,TRAVERSE_WEIGHT))
    return traverse_path

def traverse_dfs(conn, roomno, location=None):
    traverse_path = []
    stack = [(roomno,"NULL")]
    visited = set()
    last_room_no = roomno

    # sql = "select distinct(dst_room_zone) from room_and_entrance where src_room_zone = \
    # (select zone from mud_room where roomno = %d) and is_boundary = 0" % (roomno)
    
    # zones = ",".join(["'%s'" % (row[0]) for row in conn.execute(sql).fetchall()])

    while len(stack) != 0:
        (dst_room_no,dst_room_name) = stack.pop()

        if location == None or dst_room_name == location:
            if last_room_no != dst_room_no:
                traverse_path.extend(get_path_unchecked(conn, last_room_no, dst_room_no,TRAVERSE_WEIGHT))
                last_room_no = dst_room_no
            
        visited.add(dst_room_no)

        sql = "select dst_room_no, dst_room_name from room_and_entrance where src_room_no = %d and src_room_zone = dst_room_zone \
        and is_boundary = 0" % (dst_room_no)

        # sql = "select dst_room_no, dst_room_name from room_and_entrance where src_room_no = %d and dst_room_zone in (%s) \
        # and is_boundary = 0" % (dst_room_no, zones)
        
        for row in conn.execute(sql).fetchall():
            if row[0] not in visited:
                stack.append((row[0],row[1]))

    traverse_path.extend(get_path_unchecked(conn, last_room_no, roomno,TRAVERSE_WEIGHT))
    return traverse_path
    
if __name__ == "__main__":
    conn = open_database()
    roomno = int(sys.argv[1])
    if len(sys.argv) == 4:
        location = sys.argv[2]
    else:
        location = None

    sql = "select zone from mud_room where roomno = %d" % (roomno)
    row = conn.execute(sql).fetchone()
    if row and (row[0].startswith("长江") or row[0].startswith("黄河")):
        traverse_path = traverse_dfs(conn, roomno, location)
    else:
        traverse_path = traverse_bfs(conn, roomno, location)
        traverse_path.extend(traverse_dfs(conn,roomno, location))
        
    tt = Tintin()
    tt.write("#list {gps_path} create {%s}" % (";".join(traverse_path)))
