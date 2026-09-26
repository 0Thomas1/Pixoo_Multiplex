import heapq


class WorkerQueue:
	"""Priority queue for ordered task execution.

	Args:
		None.
	"""

	def __init__(self):
		self.queue = []
		self.counter = 0

	def add_task(self, priority: int, task):
		"""Add a task with a given priority (lower = higher priority).

		Args:
			priority: Priority level (lower values dequeued first).
			task: The task object to enqueue.

		Returns:
			None.
		"""
		heapq.heappush(self.queue, (priority, self.counter, task))
		self.counter += 1

	def get_task(self):
		"""Remove and return the highest-priority task.

		Args:
			None.

		Returns:
			The task with the lowest priority value.

		Raises:
			IndexError: If the queue is empty.
		"""
		if not self.queue:
			raise IndexError("get_task from an empty queue")
		_, _, task = heapq.heappop(self.queue)
		return task

	def is_empty(self):
		"""Check if the queue is empty.

		Args:
			None.

		Returns:
			True if no tasks are queued, False otherwise.
		"""
		return len(self.queue) == 0
