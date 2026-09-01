import heapq
class WorkerQueue:
    def __init__(self):
      self.queue = []
      self.counter = 0

    def add_task(self, priority: int, task):
      heapq.heappush(self.queue, (priority, self.counter, task))
      self.counter += 1

    def get_task(self):
      if not self.queue:
        raise IndexError("get_task from an empty queue")
      _, _, task = heapq.heappop(self.queue)
      return task
    
    def is_empty(self):
        return len(self.queue) == 0