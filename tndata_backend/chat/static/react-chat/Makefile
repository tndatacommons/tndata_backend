jsfile := react_chat-$(shell date -u +%y%m%d%H%M%S).js


all:

	yarn run build
	mv build/static/js/main*.js ../../static/js/$(jsfile)

	# Rename the included file in our Django template
	sed -E -i -- "s/react_chat-(.+).js/$(jsfile)/" ../../templates/chat/chat.html

	# HACK: delete the backup file, because i couldn't get sed -i to work
	#       without it.
	rm ../../templates/chat/chat.html--
