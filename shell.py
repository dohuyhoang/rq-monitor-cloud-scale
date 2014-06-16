import subprocess

deminator='--'

def exec_remote_query(url):
    return subprocess.Popen(["ssh", url, "rqueue-cli -p 6380 'keys' '*'| awk '/queues/' | awk '{print $1};' | while read line;do echo $line; rqueue-cli -p 6380 'llen' $line; echo %s ;done"%deminator], stdout=subprocess.PIPE)

def get_queues_all_size(url):
    p = exec_remote_query(url)
    return [dict([("queue", filter(None, queue.split('\n'))[0]), ("size", filter(None, queue.split('\n'))[1])]) for queue in p.communicate()[0].split(deminator) if queue.replace('\n', '')]

def get_queues_with_size(url, size):
    p = exec_remote_query(url)
    return [dict([("queue", filter(None, queue.split('\n'))[0]), ("size", filter(None, queue.split('\n'))[1])]) for queue in p.communicate()[0].split(deminator) if queue.replace('\n', '') and int(filter(None, queue.split('\n'))[1]) >= size]

