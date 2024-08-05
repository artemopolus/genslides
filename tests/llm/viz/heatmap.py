import numpy as np
import matplotlib.pyplot as plt

# Generate random data for three vectors of different lengths
vector1 = np.random.rand(10)
vector2 = np.random.rand(20)
vector3 = np.random.rand(30)

# Create a matrix of zeros for the heatmap
matrix = np.zeros((3, max(len(vector1), len(vector2), len(vector3))))

# Fill the matrix with the values from the vectors
matrix[0, :len(vector1)] = vector1
matrix[1, :len(vector2)] = vector2
matrix[2, :len(vector3)] = vector3

# Replace zero values with NaN
matrix[matrix == 0] = np.nan

# Create the heatmap
plt.imshow(matrix, cmap='viridis', aspect='auto')
plt.colorbar(label='Value')
plt.xlabel('Value Index')
plt.ylabel('Vector')
plt.title('Heatmap of Vectors')
plt.show()
