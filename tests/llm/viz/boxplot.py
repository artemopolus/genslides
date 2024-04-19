import matplotlib.pyplot as plt
import numpy as np

# Generate some random data for four vectors of different lengths
vector1 = np.random.normal(0, 1, 100)
vector2 = np.random.normal(1, 1.5, 150)
vector3 = np.random.normal(-1, 2, 120)
vector4 = np.random.normal(2, 1, 130)

# Create a list of vectors
vectors = [vector1, vector2, vector3, vector4]

# Create a box plot
plt.boxplot(vectors, labels=['Vector 1', 'Vector 2', 'Vector 3', 'Vector 4'])
plt.xlabel('Vectors')
plt.ylabel('Values')
plt.title('Comparison of Vectors with Different Lengths')
plt.grid(True)
plt.show()
