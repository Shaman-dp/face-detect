from imutils.video import VideoStream
from imutils.video import FPS
import numpy as np
import argparse
import imutils
import time
import cv2
import face_recognition
import pickle

# Initialize variables
known_face_encodings = []
known_face_metadata = []
face_locations = []
face_encodings = []

def save_known_faces():
    with open("known_faces.dat", "wb") as face_data_file:
        face_data = [known_face_encodings, known_face_metadata]
        pickle.dump(face_data, face_data_file)
        face_data_file.close()
        print("Known faces backed up to disk.")

def load_known_faces():
    global known_face_encodings, known_face_metadata

    try:
        with open("known_faces.dat", "rb") as face_data_file:
            known_face_encodings, known_face_metadata = pickle.load(face_data_file)
            face_data_file.close()
            print("Known faces loaded from disk.")
    except FileNotFoundError:
        print("No previous face data found - starting with a blank known face list.")
        pass


def register_new_face(face_encoding, face_image, face_name):
    """
    Add a new face to list of known faces
    """
    # Add the face encoding to the list of known faces
    known_face_encodings.append(face_encoding)
    # Add a matching dictionary entry to our metadata list.
    # We can use this to keep track of how many times a person has visited, when we last saw them, etc.
    known_face_metadata.append({
        "face_name": face_name,
        "face_image": face_image
    })

    save_known_faces()



def lookup_known_face(face_encoding):
    """
    See if this is a face we already have in face list
    """
    metadata = None

    # If known face list is empty, just return nothing since we can't possibly have seen this face.
    if len(known_face_encodings) == 0:
        return metadata

    # Calculate the face distance between the unknown face and every face in known face list
    # This will return a floating point number between 0.0 and 1.0 for each known face. The smaller the number,
    # the more similar that face was to the unknown face.
    face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)

    # Get the known face that had the lowest distance (i.e. most similar) from the unknown face.
    # this will return a index of min distance
    min_distance_index = np.argmin(face_distances)

    # If the face with the lowest distance had a distance under 0.6, we consider it a face match.
    # 0.6 comes from how the face recognition model was trained. It was trained to make sure pictures
    # of the same person always were less than 0.6 away from each other.
    # Here, we are loosening the threshold a little bit to 0.65 because it is unlikely that two very similar
    # people will come up to the door at the same time.
    if face_distances[min_distance_index] < 0.65:
        # If we have a match, look up the metadata we've saved for it (like the first time we saw it, etc)
        metadata = known_face_metadata[min_distance_index]

    return metadata

def main_loop():
    
    print("[INFO] starting video stream...")
    vs = VideoStream(src=0).start()
    #[VAR TWO] video_capture = cv2.VideoCapture(0)

    time.sleep(3.0)
    fps = FPS().start()

    # Track how long since we last saved a copy of our known faces to disk as a backup.
    number_of_faces_since_save = 0

    while True:
        # Grab the frame from the threaded video stream and resize it
        frame = vs.read()
        #[VAR TWO] retval, frame = video_capture.read()
        frame = imutils.resize(frame, width=300)
        #print(frame.shape)#(255,300,3)

        # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
        rgb_frame = frame[:, :, ::-1]

        # Find all the face locations and face encodings in the current frame of video
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        # Loop through each detected face and see if it is one we have seen before
        # If so, we'll give it a label that we'll draw on top of the video.
        face_labels = []

        for face_location, face_encoding in zip(face_locations, face_encodings):
            # See if this face is in list of known faces.
            metadata = lookup_known_face(face_encoding)

            # If we found the face, label the face with some useful information.
            if metadata is not None:
                # f - format
                face_label = f'You are {metadata["face_name"]}'

            # If this is a brand new face, add it to our list of known faces
            else:
                face_label = "New visitor"

                # Grab the image of the the face from the current frame of video
                top, right, bottom, left = face_location
                # обрезка по рамке
                face_image = frame[top:bottom, left:right]
                face_image = cv2.resize(face_image, (50, 50))

                # Add the new face to our known face data
                register_new_face(face_encoding, face_image, face_label)

            face_labels.append(face_label)

        # Draw a box around each face and label each face
        for (top, right, bottom, left), face_label in zip(face_locations, face_labels):

            # Draw a border around the face
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 1)

            # Draw a label with a name below the face
            cv2.rectangle(frame, (left, bottom + 20), (right, bottom), (0, 0, 255), cv2.FILLED)
            cv2.putText(frame, face_label, (left + 5, bottom + 15), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1)

        # Display recent visitor images
        lim_small_left_images = 0


        #отдельно реализовать
        for metadata in known_face_metadata:

            if lim_small_left_images == 3: break
            # If we have see this person now, draw their image
            # Draw the known face image
            y_position = lim_small_left_images * 50
            # срез многомерного массива [start:stop:step, sstart:stop:step]
            # врезка в основной frame
            frame[y_position + 30:y_position + 80, 5:55] = metadata["face_image"]
            lim_small_left_images += 1

            # Label the image with name
            cv2.putText(frame, metadata["face_name"], (70, y_position + 55), cv2.FONT_HERSHEY_DUPLEX, 0.4, (255, 255, 255), 1)

        if lim_small_left_images > 0:
            cv2.putText(frame, "Visitors at Frame:", (5, 15), cv2.FONT_HERSHEY_DUPLEX, 0.4, (255, 255, 255), 1)



        # Display the final frame of video with boxes drawn around each detected fames
        cv2.imshow('Frame', frame)

        # Hit 'q' on the keyboard to quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            # add to first seen
            save_known_faces()
            break

        # Need to save known faces back to disk every so often in case something crashes.
        if len(face_locations) > 0 and number_of_faces_since_save > 100:
            save_known_faces()
            number_of_faces_since_save = 0
        else:
            number_of_faces_since_save += 1

        # update the FPS counter
        fps.update()

    # stop the timer and display FPS information
    fps.stop()

    # format .2f for show .xx
    print("\n[INFO] work time: {:.2f}".format(fps.elapsed()))
    print("[INFO] FPS: {:.2f}".format(fps.fps()))

    #---clean all---
    #[VAR TWO] video_capture.release()
    cv2.destroyAllWindows()
    vs.stop()


if __name__ == "__main__":
    load_known_faces()
    main_loop()