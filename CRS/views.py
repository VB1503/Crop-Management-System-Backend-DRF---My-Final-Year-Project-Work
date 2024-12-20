from django.shortcuts import render
from .models import *
# from accounts.models import Landmark
from .utils import get_prediction,get_weather_data,crop_yield_pred,get_fertilizer_recommendation
from rest_framework.generics import GenericAPIView, ListCreateAPIView,RetrieveDestroyAPIView
from .serializers import CropRecommendationSerializer,LandmarkSerializer,CropYieldPredictionSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from .models import Landmark
from rest_framework.views import APIView
from rest_framework.response import Response
from .utils import get_weather_data
import os
from django.shortcuts import get_object_or_404
from django.conf import settings
from rest_framework.decorators import api_view
from django.http import JsonResponse
from django.views import View
import threading
import time


# class LandmarkDetailAPIView(RetrieveDestroyAPIView):
#     queryset = Landmark.objects.all()
#     serializer_class = LandmarkSerializer

#     def delete(self, request, *args, **kwargs):
#         instance = self.get_object()
#         serializer = self.get_serializer(instance)
#         self.perform_destroy(instance)
#         return Response(serializer.data)
    
class ListCreateLandmarkAPIView(GenericAPIView):
    queryset = Landmark.objects.all()
    serializer_class = LandmarkSerializer

    def get(self, request, *args, **kwargs):
        user_id = kwargs.get('pk')
        user = User.objects.get(pk=user_id)

        landmarks = Landmark.objects.filter(user_id=user)
        serializer = self.get_serializer(landmarks, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class DeleteLandmarkAPIView(GenericAPIView):
    queryset = Landmark.objects.all()
    serializer_class = LandmarkSerializer

    def delete(self, request, *args, **kwargs):
        user_id = kwargs.get('user_id')  # Get user_id from URL or request kwargs
        land_id = kwargs.get('landId')  # Get landId from URL or request kwargs

        # Fetch the Landmark object that matches both user_id and landId
        landmark = get_object_or_404(Landmark, user_id=user_id, landId=land_id)

        # Delete the landmark
        landmark.delete()

        # Return success response
        return Response({"message": "Landmark deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
class CropRecomendationApiView(APIView):
    serializer_class = CropRecommendationSerializer

    def post(self, request):
        crop_data = request.data
        user = crop_data.get('user')
        landId = crop_data.get('landId')

        try:
            print(crop_data)
            # Fetch Landmark object based on user and landId
            landmark = Landmark.objects.get(user=user, landId=landId)

            # Access coordinates from the Landmark object
            coordinates = landmark.coordinates

            # Calculate median latitude and longitude
            latitudes = [coord['lat'] for coord in coordinates]
            longitudes = [coord['lng'] for coord in coordinates]

            median_latitude = sum(latitudes) / len(latitudes)
            median_longitude = sum(longitudes) / len(longitudes)

            # Fetch weather data based on the median coordinates
            weather_data = get_weather_data(median_latitude, median_longitude)
            if weather_data:
                print("check")
                # Process crop recommendation data using weather data
                n = crop_data.get('nitrogen')
                p = crop_data.get('phosphorus')
                k = crop_data.get('potassium')
                ph = crop_data.get('ph')
                print(weather_data)
                prediction = get_prediction(N=n, P=p, K=k, temperature=weather_data['temp_c'], humidity=weather_data['humidity'], ph=ph, rainfall=weather_data['rainfall'], request=request)
                print(prediction)
                # Prepare data for serialization
                data = { 
                    "user": user,
                    "landId": landId, 
                    "N": n, 
                    "P": p, 
                    "K": k, 
                    "temperature": weather_data['temp_c'],  
                    "humidity": weather_data['humidity'], 
                    "ph": ph, 
                    "rainfall": weather_data['rainfall'],
                    "prediction": prediction
                }
               
                serializer = self.serializer_class(data=data)
                if serializer.is_valid(raise_exception=True):
                    serializer.save()
                    user_data = serializer.data
                    return Response({
                        'data': user_data,
                        'message': 'Thanks for using our Recommendation System'
                    }, status=status.HTTP_201_CREATED)

            else:
                print("bug")
                return Response({'success': False, 'message': 'Weather data not available'}, status=status.HTTP_400_BAD_REQUEST)

        except Landmark.DoesNotExist:
            return Response({'success': False, 'message': 'Landmark not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(str(e))
            return Response({'success': False, 'message': str(e)}, status=status.HTTP_200_OK)


class CropYieldPredictionView(APIView):
    def post(self, request, *args, **kwargs):
        crop_data = request.data

        # Extract data from the request
        user = crop_data.get('user')
        landId =crop_data.get('landId')
        year = int(crop_data.get('year'))
        season = crop_data.get('season')
        month = int(crop_data.get('month'))
        crop_type = int(crop_data.get('crop'))
        area = float(crop_data.get('area'))
        print("user:", user, type(user))
        print("landId:", landId, type(landId))
        print("year:", year, type(year))
        print("season:", season, type(season))
        print("month:", month, type(month))
        print("crop_type:", crop_type, type(crop_type))
        print("area:", area, type(area))

        # Check if the 'year' field is not null
        if not year:
            return Response({'success': False, 'message': 'Year is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Check if the Landmark exists
            landmark = Landmark.objects.get(user=user, landId=landId)

            # Access coordinates from the Landmark object
            coordinates = landmark.coordinates

            # Calculate median latitude and longitude
            latitudes = [coord['lat'] for coord in coordinates]
            longitudes = [coord['lng'] for coord in coordinates]

            median_latitude = sum(latitudes) / len(latitudes)
            median_longitude = sum(longitudes) / len(longitudes)

            # Fetch weather data based on the median coordinates
            weather_data = get_weather_data(median_latitude, median_longitude)

            if weather_data:
                # Predict crop yield
                result = crop_yield_pred(year, season, month, crop_type, area,
                                         avg_temp=weather_data['temp_c'],
                                         avg_rainfall=weather_data['rainfall'])

                

                return Response({
                    'production': result.get("production"),
                    'yield_per_hectare': result.get("yield"),
                    'message': 'Crop yield prediction successful'
                }, status=status.HTTP_200_OK)
            else:
                return Response({'success': False, 'message': 'Weather data not available'},
                                status=status.HTTP_400_BAD_REQUEST)

        except Landmark.DoesNotExist:
            return Response({'success': False, 'message': 'Landmark not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'success': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class FertilizerRecommendation(APIView):
    def post(self, request, format=None):
        # Extract data from the request
        
        temperature = request.data.get('temperature')
        humidity = request.data.get('humidity')
        moisture = request.data.get('moisture')
        soil_type = request.data.get('soil_type')
        crop_type = request.data.get('crop_type')
        nitrogen = request.data.get('nitrogen')
        phosphorous = request.data.get('phosphorous')
        potassium = request.data.get('potassium')

        # Call the utility function to get the fertilizer recommendation
        recommendation = get_fertilizer_recommendation(request=request,crop_type=crop_type, nitrogen=nitrogen, phosphorous=phosphorous, potassium=potassium,temperature=temperature,humidity=humidity,soil_type=soil_type,moisture=moisture)
      
        # Return the recommendation as a response
        return Response({"recommendation": recommendation}, status=status.HTTP_200_OK)
    


