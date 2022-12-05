import cv2

def anrp(img):
    # img = cv2.imread(img)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 11, 17, 17)
    edged = cv2.Canny(gray, 30, 200)
    cnts = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)[0]
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:30]
    count = 0
    for c in cnts:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4:  # Select the contour with 4 corners
            x, y, w, h = cv2.boundingRect(c)  # This is our approx Number Plate Contour
            new_img = img[y:y + h, x:x + w]
            count += 1
            break
    # return the cropped image
    return new_img

# read the image from a dataset in coco format
image = cv2.imread(f"{__file__}\\..\\LP_Detection\\train\\2f5a55336321e3ca_jpg.rf.27b72750a5162c4515d9ad143ded4151.jpg")

# call the anrp method
img = anrp(image)

# show the image
cv2.imshow("imag", img)
cv2.waitKey(0)