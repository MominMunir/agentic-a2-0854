from evaluation.human_panel import calibration

if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('input')
    calibration(parser.parse_args().input)
