if __name__ == "__main__":
    import sys
    with open(sys.argv[1]) as f:
        print(compile_chain([(Pipeline, "file")], f.read()))
