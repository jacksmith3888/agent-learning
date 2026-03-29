.PHONY: run test

run:
	@lecture="$(if $(L),$(L),$(word 2,$(MAKECMDGOALS)))"; \
	if [ -z "$$lecture" ]; then \
		echo "用法: make run lecture01 或 make run L=lecture01"; \
		exit 1; \
	fi; \
	./run "$$lecture" $(ARGS)

test:
	@lecture="$(if $(L),$(L),$(word 2,$(MAKECMDGOALS)))"; \
	if [ -z "$$lecture" ]; then \
		echo "用法: make test lecture01 或 make test L=lecture01"; \
		exit 1; \
	fi; \
	./test "$$lecture" $(ARGS)

%:
	@:
