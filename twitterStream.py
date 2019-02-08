from pyspark import SparkConf, SparkContext
from pyspark.streaming import StreamingContext
from pyspark.streaming.kafka import KafkaUtils
import operator
import numpy as np
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt


def main():
    conf = SparkConf().setMaster("local[2]").setAppName("Streamer")
    sc = SparkContext(conf=conf)
    sc.setLogLevel("WARN")
    ssc = StreamingContext(sc, 10)   # Create a streaming context with batch interval of 10 sec
    ssc.checkpoint("checkpoint")

    pwords = load_wordlist("positive.txt")
    nwords = load_wordlist("negative.txt")

    counts = stream(ssc, pwords, nwords, 100)

    make_plot(counts)


def make_plot(counts):
    """
    Plot the counts for the positive and negative words for each timestep.
    Use plt.show() so that the plot will popup.
    """
    # YOUR CODE HERE
    p_vals = []
    n_vals = []

    for x in counts:
        if x :
            p_vals.append(x[0][1])
            n_vals.append(x[1][1])

    plt.plot(p_vals,label='positive',marker='o')
    plt.plot(n_vals,label='negative',marker='o')
    plt.legend(loc='upper left')
    plt.xticks(np.arange(0, len(counts), 1))
    plt.ylim(ymin=0,ymax=max(max(p_vals),max(n_vals))+20)
    plt.xlabel("Time Step")
    plt.ylabel("Word Count")
    plt.savefig("Plot")



def load_wordlist(filename):
    """
    This function should return a list or set of words from the given filename.
    """
    # YOUR CODE HERE
    data=open(filename,'r')
    data=data.read()
    data=data.split('\n')
    data = set(data)

    return data

def updateFunction(newValues, runningCount):
    if runningCount is None:
       runningCount = 0
    return sum(newValues, runningCount)

def stream(ssc, pwords, nwords, duration):
    kstream = KafkaUtils.createDirectStream(
        ssc, topics = ['twitterstream'], kafkaParams = {"metadata.broker.list": 'localhost:9092'})
    tweets = kstream.map(lambda x: x[1].encode("ascii","ignore"))

    # Each element of tweets will be the text of a tweet.
    # You need to find the count of all the positive and negative words in these tweets.
    # Keep track of a running total counts and print this at every time step (use the pprint function).
    # YOUR CODE HERE
    words_stream = tweets.map(lambda line: line.lower()).flatMap(lambda line: line.split(" "))
    positive_words = words_stream.filter(lambda x: x in pwords)
    negative_words = words_stream.filter(lambda x: x in nwords)

    p_count = positive_words.map(lambda x: ('positive',1)).reduceByKey(lambda x, y: x + y)
    n_count = negative_words.map(lambda x: ('negative',1)).reduceByKey(lambda x, y: x + y)
    wordCount = p_count.union(n_count)

    runningCounts = wordCount.updateStateByKey(updateFunction)

    runningCounts.pprint()

    # Let the counts variable hold the word counts for all time steps
    # You will need to use the foreachRDD function.
    # For our implementation, counts looked like:
    #   [[("positive", 100), ("negative", 50)], [("positive", 80), ("negative", 60)], ...]
    counts = []

    wordCount.foreachRDD(lambda t,rdd: counts.append(rdd.collect()))
    ssc.start()                         # Start the computation
    ssc.awaitTerminationOrTimeout(duration)
    ssc.stop(stopGraceFully=True)

    return counts


if __name__=="__main__":
    main()
