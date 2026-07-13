# TDD Language Reference

Test runner commands by language. Use these for RED (verify fail) and GREEN (verify pass) phases.

## Go

```bash
go test ./...                            # All tests
go test ./path/to/package -run TestName  # Single test
go test ./... -v                         # Verbose output
go test ./... -cover                     # With coverage
```

## TypeScript (Vitest)

```bash
npm test                                 # All tests
npm test -- -t "test name"              # Single test
npx vitest run                           # CI mode (no watch)
npm test -- --coverage                   # With coverage
```

## TypeScript (Jest)

```bash
npm test                                 # All tests
npm test -- -t "test name"              # Single test
npx jest --no-cache                      # Clear cache
npm test -- --coverage                   # With coverage
```

## Rust

```bash
cargo test                               # All tests
cargo test test_name                     # Single test
cargo test -- --nocapture                # With output
cargo test -- --test-threads=1           # Sequential
```

## Python (pytest)

```bash
pytest                                   # All tests
pytest -k "test_name"                    # Single test
pytest path/to/test_file.py              # Single file
pytest --cov                             # With coverage
pytest -x                                # Stop on first failure
```

## Ruby (RSpec)

```bash
bundle exec rspec                        # All tests
bundle exec rspec spec/path/file_spec.rb # Single file
bundle exec rspec -e "test name"         # Single test
bundle exec rspec --format documentation # Verbose
```

## Ruby (Minitest)

```bash
ruby -Itest test/test_file.rb            # Single file
rake test                                # All tests
ruby -Itest test/test_file.rb -n test_name # Single test
```

## Elixir

```bash
mix test                                 # All tests
mix test test/path/file_test.exs         # Single file
mix test test/path/file_test.exs:42      # Single test (line)
mix test --cover                         # With coverage
```

## Java (JUnit + Maven)

```bash
mvn test                                 # All tests
mvn test -Dtest=ClassName                # Single class
mvn test -Dtest=ClassName#methodName     # Single test
```

## C# (.NET)

```bash
dotnet test                              # All tests
dotnet test --filter "TestName"          # Single test
dotnet test --collect:"XPlat Code Coverage" # With coverage
```
