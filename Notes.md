## Pseudo Code
```
Client:
	while True:
		try:
			send(data)
		except interruption:
			close()
```

```
Server:
	channel = 0
	while true:
		consume(channel)
		

		