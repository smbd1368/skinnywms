from skinnywms.wmssvr import application


__all__ = [
    "main",
]


def main():
    application.run(debug=True, threaded=True)


if __name__ == "__main__":
    main()
